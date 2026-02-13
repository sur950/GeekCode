"""
Workspace Query Layer — gather live project data for the LLM.

Three kinds of context gathering:

1. **Shell queries** — git log, git status, etc. (read-only commands)
2. **File discovery** — find and read code/config files relevant to the task
3. **Document parsing** — locate and extract content from docs, READMEs, etc.

The agent calls ``gather_workspace_context(task, workspace)`` before building
the prompt.  Only read-only operations are performed; nothing is modified.
"""

import fnmatch
import hashlib
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ── Ignore patterns (never read these) ────────────────────────────────────────

_IGNORE_DIRS = {
    # VCS
    ".git", ".hg", ".svn",
    # Python
    "__pycache__", ".tox", ".mypy_cache", ".pytest_cache", ".eggs",
    "venv", ".venv", "env", ".env",
    # JS / Node
    "node_modules", ".next", ".nuxt", ".turbo", "bower_components",
    # Build output (multi-lang)
    "dist", "build", "out", "bin", "obj", "target", "release", "debug",
    # JVM
    ".gradle", ".m2", ".ivy2",
    # iOS / macOS
    "Pods", ".build", "DerivedData",
    # Go / PHP / Ruby
    "vendor",
    # Misc
    ".geekcode", "coverage", ".coverage", ".nyc_output",
}

_IGNORE_EXTS = {
    # Compiled / binary
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe", ".o", ".a", ".lib",
    ".class", ".dex",
    # Archives
    ".whl", ".egg", ".tar", ".gz", ".zip", ".jar", ".war", ".aar",
    ".tgz", ".bz2", ".xz", ".rar", ".7z",
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".bmp", ".webp",
    # Fonts
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    # Minified / generated
    ".lock", ".min.js", ".min.css", ".map",
    # Data blobs
    ".sqlite", ".db", ".bin", ".dat", ".pkl", ".npy", ".npz",
    # Media
    ".mp3", ".mp4", ".mov", ".avi", ".wav", ".pdf",
}

_MAX_FILE_SIZE = 50_000       # 50 KB — skip files larger than this in walk/search
_MAX_DOC_SIZE = 2_000_000     # 2 MB — docs can be larger; we'll read a snippet
_MAX_READ_SIZE = 500_000      # 500 KB — hard cap on bytes read from any single file


# ═══════════════════════════════════════════════════════════════════════════════
#  1. Shell query patterns  (git, disk, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

_SHELL_PATTERNS: List[Tuple[re.Pattern, str, List[str]]] = [
    # Git history / commits
    (
        re.compile(
            r"\b(last|recent|latest|previous)\b.*\b(commit|commits|push|pushed|change|changes)\b"
            r"|\b(commit|commits)\b.*\b(last|recent|latest|previous|history|log)\b"
            r"|\bgit\s+log\b"
            r"|\bcommit\s+history\b"
            r"|\bwho\s+committed\b"
            r"|\bwhen\s+.*(commit|push|change)",
            re.IGNORECASE,
        ),
        "Recent commits",
        ["git", "log", "--oneline", "--no-decorate", "-15"],
    ),
    # Git status / working tree
    (
        re.compile(
            r"\b(git\s+)?status\b"
            r"|\buncommitted\b|\bunstaged\b|\bstaged\b"
            r"|\bmodified\s+files\b|\bchanged\s+files\b|\buntracked\b"
            r"|\bworking\s+(tree|directory)\b",
            re.IGNORECASE,
        ),
        "Git status",
        ["git", "status", "--short"],
    ),
    # Git diff
    (
        re.compile(
            r"\b(git\s+)?diff\b"
            r"|\bwhat\s+(changed|was\s+changed|has\s+changed)\b"
            r"|\bshow\s+(me\s+)?the\s+changes\b",
            re.IGNORECASE,
        ),
        "Git diff",
        ["git", "diff", "--stat"],
    ),
    # Current branch
    (
        re.compile(
            r"\b(current|active|which)\s+branch\b"
            r"|\bbranch\s+(name|am\s+i|are\s+we)\b"
            r"|\bgit\s+branch\b",
            re.IGNORECASE,
        ),
        "Git branch",
        ["git", "branch", "--show-current"],
    ),
    # All branches
    (
        re.compile(
            r"\b(list|show|all)\s+branch(es)?\b|\bbranches\b",
            re.IGNORECASE,
        ),
        "Git branches",
        ["git", "branch", "-a"],
    ),
    # Git remotes
    (
        re.compile(
            r"\b(git\s+)?remote(s)?\b|\borigin\b.*\burl\b|\bupstream\b",
            re.IGNORECASE,
        ),
        "Git remotes",
        ["git", "remote", "-v"],
    ),
    # File / directory listing / project structure
    (
        re.compile(
            r"\b(project|directory|folder|file)\s+(structure|tree|layout|listing)\b"
            r"|\blist\s+(the\s+)?(files|directories|folders)\b"
            r"|\bwhat\s+files\b"
            r"|\bshow\s+(me\s+)?(the\s+)?files\b"
            r"|\btree\b",
            re.IGNORECASE,
        ),
        "Project structure",
        ["git", "ls-files"],
    ),
    # Git tags / versions / releases
    (
        re.compile(
            r"\btags?\b"
            r"|\b(latest|current|last)\s+version\b"
            r"|\breleases?\b"
            r"|\bversions?\b.*\b(list|show|all)\b",
            re.IGNORECASE,
        ),
        "Git tags",
        ["git", "tag", "--sort=-creatordate", "-n1"],
    ),
    # Contributors / authors
    (
        re.compile(
            r"\b(contributors?|authors?|who)\b.*\b(commit|wrote|contributed|worked)\b"
            r"|\bcontributors?\b|\bgit\s+shortlog\b",
            re.IGNORECASE,
        ),
        "Contributors",
        ["git", "shortlog", "-sn", "--no-merges", "HEAD"],
    ),
    # Stash
    (
        re.compile(r"\bstash(es|ed)?\b", re.IGNORECASE),
        "Git stash",
        ["git", "stash", "list"],
    ),
    # Disk usage / size
    (
        re.compile(
            r"\b(disk|size|space)\b.*\b(usage|used|taken)\b"
            r"|\bhow\s+(big|large)\b",
            re.IGNORECASE,
        ),
        "Disk usage",
        ["du", "-sh", "."],
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
#  2. File discovery — find code/config files relevant to the task
# ═══════════════════════════════════════════════════════════════════════════════

# Regex to extract file references from the user's task
# Covers: Python, JS/TS, Go, Rust, Java/Kotlin/Scala, C/C++/C#, Swift, Ruby,
# PHP, Dart, Elixir, Lua, R, Zig, Nim, Haskell, Perl, Shell, configs, markup
_FILE_REF_EXTS = (
    # Core languages
    r"py|js|ts|tsx|jsx|mjs|cjs|go|rs|java|kt|kts|scala|sbt"
    r"|c|cpp|cc|cxx|h|hpp|hxx|cs|fs|fsx"
    r"|swift|m|mm"                          # Apple
    r"|rb|erb"                              # Ruby
    r"|php|phtml"                           # PHP
    r"|dart"                                # Dart
    r"|ex|exs|erl|hrl"                      # Elixir / Erlang
    r"|lua|r|R|jl"                          # Lua, R, Julia
    r"|zig|nim|v|hx"                        # Zig, Nim, V, Haxe
    r"|hs|lhs|ml|mli|clj|cljs|cljc|edn"    # Haskell, OCaml, Clojure
    r"|pl|pm|p6|raku"                       # Perl
    r"|sh|bash|zsh|fish|ps1|psm1|bat|cmd"   # Shell / PowerShell
    # Config / data
    r"|yaml|yml|json|toml|xml|ini|cfg|conf|env|properties"
    # Markup / style
    r"|html|htm|css|scss|less|sass|vue|svelte|astro"
    # Other
    r"|sql|graphql|gql|proto|tf|hcl|dockerfile|cmake"
    r"|md|txt|rst|adoc|tex"
)
_FILE_REF = re.compile(
    rf"(?:in|from|file|at|of|the)\s+[`'\"]?(\w[\w./\\-]+\.(?:{_FILE_REF_EXTS}))[`'\"]?",
    re.IGNORECASE,
)

# Regex to extract function / class / variable names the user might be asking about
# Keywords across languages: Python def/class, JS/TS function/const/let/var/type/interface,
# Go func/type/struct/interface, Rust fn/struct/enum/trait/impl, Java/Kotlin class/fun/val/object,
# Scala def/val/object/trait/case, Swift func/class/struct/protocol/extension,
# C# class/struct/interface/record, PHP class/function/trait, Dart class/mixin,
# Elixir def/defp/defmodule, Ruby def/class/module
_SYMBOL_REF = re.compile(
    r"(?:function|method|class|def|defp|defmodule|fn|func|fun|sub|val|object|trait|impl|"
    r"protocol|extension|mixin|record|module|package|"
    r"variable|const|var|let|type|interface|struct|enum)\s+[`'\"]?(\w+)[`'\"]?",
    re.IGNORECASE,
)

# Broad "explain/describe/how does X work" pattern that implies needing to read code
_CODE_QUESTION = re.compile(
    r"\b(explain|describe|how\s+does|what\s+does|what\s+is|where\s+is|find|show\s+me|read|look\s+at|understand)\b",
    re.IGNORECASE,
)


def _is_ignored(path: Path) -> bool:
    """Check if a path should be ignored."""
    for part in path.parts:
        if part in _IGNORE_DIRS:
            return True
    return path.suffix.lower() in _IGNORE_EXTS


def _walk_project_files(workspace: Path, max_files: int = 5000) -> List[Path]:
    """Walk the workspace collecting indexable files."""
    files = []
    for root, dirs, filenames in os.walk(workspace):
        # Prune ignored directories in-place
        dirs[:] = [d for d in dirs if d not in _IGNORE_DIRS]
        for name in filenames:
            p = Path(root) / name
            if not _is_ignored(p) and p.stat().st_size <= _MAX_FILE_SIZE:
                files.append(p)
                if len(files) >= max_files:
                    return files
    return files


def find_files_by_name(task: str, workspace: Path) -> List[Path]:
    """Extract explicit file references from the task and locate them."""
    found = []
    for match in _FILE_REF.finditer(task):
        ref = match.group(1)
        # Try exact path first
        exact = workspace / ref
        if exact.exists() and exact.is_file():
            found.append(exact)
            continue
        # Glob search
        for p in workspace.rglob(f"*{ref}"):
            if p.is_file() and not _is_ignored(p):
                found.append(p)
                break
    return found


def find_files_by_symbol(task: str, workspace: Path) -> List[Tuple[Path, str]]:
    """Search for symbol definitions (function/class names) in code files."""
    symbols = _SYMBOL_REF.findall(task)
    if not symbols:
        return []

    results = []
    project_files = _walk_project_files(workspace, max_files=2000)
    code_exts = {
        # Python
        ".py",
        # JS / TS
        ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs", ".vue", ".svelte",
        # Systems
        ".go", ".rs", ".c", ".cpp", ".cc", ".cxx", ".h", ".hpp", ".hxx", ".zig", ".nim", ".v",
        # JVM
        ".java", ".kt", ".kts", ".scala",
        # .NET
        ".cs", ".fs", ".fsx",
        # Apple
        ".swift", ".m", ".mm",
        # Scripting
        ".rb", ".php", ".lua", ".pl", ".pm", ".r", ".R", ".jl",
        # Dart / Elixir / Erlang
        ".dart", ".ex", ".exs", ".erl",
        # Functional
        ".hs", ".ml", ".mli", ".clj", ".cljs",
        # Haxe
        ".hx",
    }

    for sym in symbols[:3]:  # Cap at 3 symbols to avoid slowness
        pattern = re.compile(
            rf"\b(def|defp|defmodule|class|data\s+class|case\s+class|object|"
            rf"function|func|fun|fn|pub\s+fn|sub|"
            rf"val|var|const|let|"
            rf"type|interface|struct|enum|trait|impl|"
            rf"protocol|extension|mixin|record|module|package)\s+{re.escape(sym)}\b"
        )
        for p in project_files:
            if p.suffix.lower() not in code_exts:
                continue
            try:
                content = p.read_text(errors="ignore")
                if pattern.search(content):
                    results.append((p, sym))
                    break  # First match per symbol
            except Exception:
                continue

    return results


def _split_identifiers(text: str) -> set:
    """Split text into words, also breaking apart snake_case and camelCase."""
    # First extract all word-like tokens (including underscored identifiers)
    tokens = re.findall(r"[a-zA-Z_]{3,}", text.lower())
    words = set()
    for token in tokens:
        words.add(token)
        # Also split on underscores (process_payment → process, payment)
        for part in token.split("_"):
            if len(part) >= 3:
                words.add(part)
    return words


def find_files_by_content(task: str, workspace: Path, max_results: int = 3) -> List[Tuple[Path, float]]:
    """Score project files by keyword overlap with the task (fallback search)."""
    task_words = _split_identifiers(task)
    # Remove common English words that aren't useful for code search
    stop_words = {
        "the", "and", "for", "that", "this", "with", "from", "have", "has",
        "how", "does", "what", "where", "when", "why", "can", "which",
        "show", "explain", "find", "look", "help", "about", "into",
        "file", "code", "function", "class", "method", "please", "want",
    }
    task_words -= stop_words
    if not task_words:
        return []

    project_files = _walk_project_files(workspace, max_files=2000)
    scored: List[Tuple[Path, float]] = []

    for p in project_files:
        try:
            content = p.read_text(errors="ignore").lower()
            content_words = _split_identifiers(content)
            overlap = len(task_words & content_words)
            if overlap >= 2:
                # Boost for filename matching task words
                name_words = _split_identifiers(p.stem)
                name_overlap = len(task_words & name_words)
                score = overlap + name_overlap * 3
                scored.append((p, score))
        except Exception:
            continue

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:max_results]


# ═══════════════════════════════════════════════════════════════════════════════
#  3. Document parsing — read docs, READMEs, markdown, text
# ═══════════════════════════════════════════════════════════════════════════════

_DOC_QUESTION = re.compile(
    r"\b(readme|documentation|docs?|guide|policy|report|spec|specification|manual|license|changelog|contributing)\b",
    re.IGNORECASE,
)

_DOC_PATTERNS = ["README*", "*.md", "*.txt", "*.rst", "docs/**/*", "doc/**/*"]


def find_relevant_docs(task: str, workspace: Path) -> List[Path]:
    """Find document files that match the user's query."""
    doc_refs = _DOC_QUESTION.findall(task)
    if not doc_refs:
        return []

    candidates: List[Tuple[Path, int]] = []
    task_lower = task.lower()

    for pattern in _DOC_PATTERNS:
        for p in workspace.glob(pattern):
            if p.is_file() and not _is_ignored(p) and p.stat().st_size <= _MAX_FILE_SIZE:
                score = 0
                name_lower = p.stem.lower()
                # Score by how well the filename matches the doc reference
                for ref in doc_refs:
                    if ref.lower() in name_lower:
                        score += 10
                # Also score by task keyword overlap in filename
                for word in re.findall(r"[a-zA-Z]{3,}", task_lower):
                    if word in name_lower:
                        score += 2
                if score > 0:
                    candidates.append((p, score))

    candidates.sort(key=lambda x: x[1], reverse=True)
    # Deduplicate (a file may match multiple glob patterns)
    seen = set()
    unique = []
    for p, _ in candidates:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique[:2]


# ═══════════════════════════════════════════════════════════════════════════════
#  4. Project summary — always-on baseline context
# ═══════════════════════════════════════════════════════════════════════════════

_TECH_STACK_FILES = {
    "package.json": "Node.js",
    "pyproject.toml": "Python",
    "setup.py": "Python",
    "setup.cfg": "Python",
    "requirements.txt": "Python",
    "go.mod": "Go",
    "Cargo.toml": "Rust",
    "pom.xml": "Java",
    "build.gradle": "Java/Kotlin",
    "build.gradle.kts": "Kotlin",
    "Gemfile": "Ruby",
    "composer.json": "PHP",
    "pubspec.yaml": "Dart/Flutter",
    "mix.exs": "Elixir",
}

_TECH_STACK_GLOBS = {
    "*.sln": ".NET",
    "*.csproj": ".NET",
}


def _detect_tech_stack(workspace: Path) -> str:
    """Detect tech stack from config files in the workspace root."""
    detected = []

    for filename, lang in _TECH_STACK_FILES.items():
        config_path = workspace / filename
        if not config_path.exists():
            continue

        info = lang
        try:
            content = config_path.read_text(errors="ignore")
            if filename == "package.json":
                import json
                data = json.loads(content)
                name = data.get("name", "")
                deps = list(data.get("dependencies", {}).keys())[:10]
                if name:
                    info += f" ({name})"
                if deps:
                    info += f", deps: {', '.join(deps)}"
            elif filename == "pyproject.toml":
                # Extract project name and dependencies
                name_match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
                if name_match:
                    info += f" ({name_match.group(1)})"
                # Look for dependencies list
                dep_matches = re.findall(r'"([a-zA-Z][\w-]*)(?:[><=!].*?)?"', content)
                if dep_matches:
                    info += f", deps: {', '.join(dep_matches[:10])}"
            elif filename == "requirements.txt":
                lines = [l.strip().split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
                         for l in content.splitlines() if l.strip() and not l.startswith("#")]
                if lines:
                    info += f", deps: {', '.join(lines[:10])}"
            elif filename == "go.mod":
                mod_match = re.search(r'^module\s+(\S+)', content, re.MULTILINE)
                if mod_match:
                    info += f" ({mod_match.group(1)})"
            elif filename == "Cargo.toml":
                name_match = re.search(r'^name\s*=\s*"([^"]+)"', content, re.MULTILINE)
                if name_match:
                    info += f" ({name_match.group(1)})"
        except Exception:
            pass

        detected.append(info)

    # Check glob patterns (.sln, .csproj)
    for pattern, lang in _TECH_STACK_GLOBS.items():
        if any(workspace.glob(pattern)):
            detected.append(lang)

    if not detected:
        return ""
    return "Tech stack: " + "; ".join(detected)


def _build_file_tree(workspace: Path) -> str:
    """Build a compact file tree for the project summary.

    For projects with ≤300 files, list all files.
    For larger projects, show directory structure with file counts.
    """
    # Try git ls-files first (respects .gitignore)
    file_list = []
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, timeout=10,
            cwd=str(workspace),
        )
        if result.returncode == 0 and result.stdout.strip():
            file_list = [l for l in result.stdout.strip().splitlines() if l.strip()]
    except Exception:
        pass

    # Fallback to walking the project
    if not file_list:
        walked = _walk_project_files(workspace, max_files=2000)
        file_list = []
        for p in walked:
            try:
                file_list.append(str(p.relative_to(workspace)))
            except ValueError:
                file_list.append(str(p))

    if not file_list:
        return "(no files found)"

    # Small projects: list all files
    if len(file_list) <= 300:
        tree = "\n".join(sorted(file_list))
        # Cap output at ~8KB
        if len(tree) > 8000:
            lines = tree.split("\n")
            tree = "\n".join(lines[:200]) + f"\n... ({len(lines) - 200} more files)"
        return tree

    # Large projects: show directory structure with file counts
    dir_counts: Dict[str, int] = {}
    top_files = []
    for f in file_list:
        parts = f.split("/")
        if len(parts) == 1:
            top_files.append(f)
        else:
            # Group by top-level and second-level directory
            key = "/".join(parts[:2]) + "/" if len(parts) > 2 else "/".join(parts[:1]) + "/"
            dir_counts[key] = dir_counts.get(key, 0) + 1

    lines = []
    for f in sorted(top_files):
        lines.append(f)
    for d in sorted(dir_counts.keys()):
        lines.append(f"{d} ({dir_counts[d]} files)")

    tree = "\n".join(lines)
    if len(tree) > 8000:
        lines = tree.split("\n")
        tree = "\n".join(lines[:200]) + f"\n... ({len(lines) - 200} more entries)"
    return tree


def _get_file_list_hash(workspace: Path) -> str:
    """Get a hash of the file listing for cache invalidation."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, timeout=10,
            cwd=str(workspace),
        )
        if result.returncode == 0 and result.stdout.strip():
            return hashlib.sha256(result.stdout.encode()).hexdigest()[:16]
    except Exception:
        pass

    # Fallback: hash the walked file list
    walked = _walk_project_files(workspace, max_files=2000)
    listing = "\n".join(sorted(str(p) for p in walked))
    return hashlib.sha256(listing.encode()).hexdigest()[:16]


def build_project_summary(workspace: Path) -> str:
    """Build an always-on baseline project summary.

    Returns a formatted string with:
    - File tree (compact)
    - README snippet (first 80 lines)
    - Tech stack detection

    Results are cached in .geekcode/context/project_summary.txt and
    regenerated only when the file listing hash changes.
    """
    geekcode_dir = workspace / ".geekcode"
    context_dir = geekcode_dir / "context"
    cache_file = context_dir / "project_summary.txt"
    hash_file = context_dir / "project_summary_hash.txt"

    # Check cache validity
    current_hash = _get_file_list_hash(workspace)
    if cache_file.exists() and hash_file.exists():
        try:
            cached_hash = hash_file.read_text().strip()
            if cached_hash == current_hash:
                return cache_file.read_text()
        except Exception:
            pass

    # Build fresh summary
    parts = []

    # a) File tree
    file_tree = _build_file_tree(workspace)
    if file_tree:
        parts.append(f"### File Tree\n```\n{file_tree}\n```")

    # b) README snippet
    for readme_name in ("README.md", "README", "README.rst", "README.txt", "readme.md"):
        readme_path = workspace / readme_name
        if readme_path.exists() and readme_path.is_file():
            try:
                content = readme_path.read_text(errors="ignore")
                lines = content.split("\n")
                snippet = "\n".join(lines[:80])
                if len(lines) > 80:
                    snippet += f"\n... ({len(lines) - 80} more lines)"
                parts.append(f"### README ({readme_name})\n```\n{snippet}\n```")
            except Exception:
                pass
            break

    # c) Tech stack
    tech = _detect_tech_stack(workspace)
    if tech:
        parts.append(f"### {tech}")

    summary = "\n\n".join(parts)

    # Cache the result
    try:
        context_dir.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(summary)
        hash_file.write_text(current_hash)
    except Exception:
        pass

    return summary


# ═══════════════════════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════════════════════

def detect_queries(task: str) -> List[Tuple[str, List[str]]]:
    """Return (label, command) pairs for shell patterns matched by the task."""
    matched = []
    seen_labels = set()
    for pattern, label, command in _SHELL_PATTERNS:
        if pattern.search(task) and label not in seen_labels:
            matched.append((label, command))
            seen_labels.add(label)
    return matched


def run_query(command: List[str], workspace: Path, timeout: int = 10) -> str:
    """Execute a single read-only query command. Returns output or error string."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(workspace),
        )
        output = (result.stdout or "").strip()
        if not output and result.stderr:
            output = result.stderr.strip()
        if not output:
            output = "(no output)"
        # Truncate very long output
        if len(output) > 3000:
            lines = output.split("\n")
            output = "\n".join(lines[:60]) + f"\n... ({len(lines) - 60} more lines)"
        return output
    except subprocess.TimeoutExpired:
        return "(command timed out)"
    except FileNotFoundError:
        return "(command not found)"
    except Exception as e:
        return f"(error: {e})"


def _read_file_snippet(path: Path, max_lines: int = 80) -> str:
    """Read a file, truncating to max_lines if large.

    Safety: never reads more than _MAX_READ_SIZE bytes into memory, even for
    multi-hundred-MB assets.  Binary files are detected and skipped.
    """
    try:
        size = path.stat().st_size
        if size > _MAX_READ_SIZE:
            # Read only the head; don't load the whole file
            with open(path, "r", errors="ignore") as f:
                head = f.read(_MAX_READ_SIZE)
            lines = head.split("\n")
            head_lines = lines[:40]
            return "\n".join(
                head_lines
                + [f"... (file is {size / 1_000_000:.1f} MB — showing first {len(head_lines)} lines) ..."]
            )

        content = path.read_text(errors="ignore")

        # Quick binary check: if more than 10% of the first 1024 bytes are
        # non-text, treat as binary.
        sample = content[:1024]
        if sample and sum(1 for c in sample if c == "\x00") > len(sample) * 0.1:
            return f"(binary file, {size / 1_000:.0f} KB — skipped)"

        lines = content.split("\n")
        if len(lines) <= max_lines:
            return content
        return "\n".join(
            lines[:40]
            + [f"... ({len(lines) - 60} lines omitted) ..."]
            + lines[-20:]
        )
    except Exception as e:
        return f"(error reading: {e})"


def gather_workspace_context(task: str, workspace: Path) -> Optional[str]:
    """
    Detect what live workspace data the task needs, gather it, and return
    a formatted context block.  Returns None if nothing relevant found.

    Checks (in order):
    1. Shell queries (git log, status, etc.)
    2. Explicit file references (``in agent.py``, ``file main.go``)
    3. Symbol search (``function run``, ``class Agent``)
    4. Document search (``readme``, ``docs``, ``policy``)
    5. Content-based file search (fallback keyword match)
    """
    parts: List[str] = []

    # ── 1. Shell queries ──────────────────────────────────────────────
    shell_queries = detect_queries(task)
    for label, command in shell_queries:
        output = run_query(command, workspace)
        parts.append(f"### {label}\n```\n{output}\n```")

    # ── 2. Explicit file references ───────────────────────────────────
    named_files = find_files_by_name(task, workspace)
    for fp in named_files[:3]:
        rel = fp.relative_to(workspace) if fp.is_relative_to(workspace) else fp
        snippet = _read_file_snippet(fp)
        parts.append(f"### File: {rel}\n```\n{snippet}\n```")

    # ── 3. Symbol search (function/class definitions) ─────────────────
    if not named_files:
        symbol_hits = find_files_by_symbol(task, workspace)
        for fp, sym in symbol_hits[:3]:
            rel = fp.relative_to(workspace) if fp.is_relative_to(workspace) else fp
            snippet = _read_file_snippet(fp)
            parts.append(f"### File: {rel} (contains `{sym}`)\n```\n{snippet}\n```")

    # ── 4. Document search ────────────────────────────────────────────
    docs = find_relevant_docs(task, workspace)
    for fp in docs:
        rel = fp.relative_to(workspace) if fp.is_relative_to(workspace) else fp
        snippet = _read_file_snippet(fp, max_lines=60)
        parts.append(f"### Document: {rel}\n```\n{snippet}\n```")

    # ── 5. Fallback: content-based file search ────────────────────────
    if not parts and _CODE_QUESTION.search(task):
        content_hits = find_files_by_content(task, workspace)
        for fp, _score in content_hits:
            rel = fp.relative_to(workspace) if fp.is_relative_to(workspace) else fp
            snippet = _read_file_snippet(fp)
            parts.append(f"### File: {rel}\n```\n{snippet}\n```")

    return "\n\n".join(parts) if parts else None
