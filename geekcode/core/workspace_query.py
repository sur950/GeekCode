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
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ── Ignore patterns (never read these) ────────────────────────────────────────

_IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".tox",
    ".mypy_cache", ".pytest_cache", "dist", "build", ".eggs",
    "venv", ".venv", "env", ".env", ".geekcode",
}

_IGNORE_EXTS = {
    ".pyc", ".pyo", ".so", ".dylib", ".dll", ".exe",
    ".whl", ".egg", ".tar", ".gz", ".zip", ".jar",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".woff", ".woff2", ".ttf", ".eot",
    ".lock", ".min.js", ".min.css",
}

_MAX_FILE_SIZE = 50_000  # 50 KB


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
_FILE_REF = re.compile(
    r"(?:in|from|file|at|of|the)\s+[`'\"]?(\w[\w./\\-]+\.(?:py|js|ts|tsx|jsx|go|rs|java|rb|c|cpp|h|yaml|yml|json|toml|md|txt|cfg|ini|sh|bash|html|css|sql))[`'\"]?",
    re.IGNORECASE,
)

# Regex to extract function / class / variable names the user might be asking about
_SYMBOL_REF = re.compile(
    r"(?:function|method|class|def|fn|func|variable|const|var|let|type|interface|struct|enum)\s+[`'\"]?(\w+)[`'\"]?",
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
    code_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".c", ".cpp", ".h"}

    for sym in symbols[:3]:  # Cap at 3 symbols to avoid slowness
        pattern = re.compile(
            rf"\b(def|class|function|func|fn|const|let|var|type|interface|struct|enum)\s+{re.escape(sym)}\b"
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
    """Read a file, truncating to max_lines if large."""
    try:
        content = path.read_text(errors="ignore")
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
