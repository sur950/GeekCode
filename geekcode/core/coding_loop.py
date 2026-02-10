"""
GeekCode Coding Loop - Agentic edit-test-iterate loop.

Reads files, asks LLM for edits, applies them, runs tests, and iterates
until tests pass or max iterations reached. All state checkpointed to
.geekcode/loop/ for crash recovery and resume.

Token-efficient: each iteration sends only the task + current file contents
+ last test output. No conversation history accumulation.
"""

import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Edit:
    """A single file edit or creation."""

    file_path: str
    old_content: str  # empty for CREATE
    new_content: str
    is_create: bool = False


@dataclass
class IterationResult:
    """Result of a single edit-test iteration."""

    iteration: int
    edits_applied: List[Dict[str, Any]]
    test_command: Optional[str]
    test_passed: bool
    test_output: str
    tokens_used: int = 0


@dataclass
class LoopResult:
    """Final result of the coding loop."""

    task: str
    iterations: List[IterationResult]
    total_tokens: int
    success: bool
    final_output: str


# ---------------------------------------------------------------------------
# Heuristic: is this a coding task?
# ---------------------------------------------------------------------------

_CODING_VERBS = {
    "fix", "add", "implement", "refactor", "update", "change", "modify",
    "write", "create", "delete", "remove", "rename", "move", "extract",
    "optimize", "improve", "debug", "patch", "rewrite", "convert",
}

_CODING_NOUNS = {
    "function", "method", "class", "module", "test", "tests", "bug",
    "error", "endpoint", "route", "handler", "middleware", "model",
    "schema", "migration", "config", "component", "service", "api",
    "interface", "type", "enum", "struct", "trait", "decorator",
    "validator", "serializer", "controller", "factory", "helper",
}


def is_coding_task(task: str) -> bool:
    """Heuristic: does this task look like a code modification request?"""
    words = set(task.lower().split())
    has_verb = bool(words & _CODING_VERBS)
    has_noun = bool(words & _CODING_NOUNS)
    has_file_ref = bool(re.search(r'\w+\.\w{1,5}\b', task))  # file.ext pattern
    return (has_verb and has_noun) or (has_verb and has_file_ref)


# ---------------------------------------------------------------------------
# CodingLoop
# ---------------------------------------------------------------------------

class CodingLoop:
    """
    Agentic edit-test loop with filesystem checkpointing.

    Each iteration:
    1. Build a minimal prompt (task + file contents + last test output)
    2. Ask the LLM for edits in <<<EDIT>>> format
    3. Parse and apply edits to the filesystem
    4. Run the detected test command
    5. If tests pass → done. If not → iterate.
    6. Checkpoint state after every iteration.
    """

    def __init__(self, workspace: Path, geekcode_dir: Path):
        self.workspace = Path(workspace)
        self.geekcode_dir = Path(geekcode_dir)
        self.loop_dir = self.geekcode_dir / "loop"
        self.loop_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        task: str,
        files: List[str],
        config: Optional[Dict[str, Any]] = None,
        max_iterations: int = 5,
    ) -> LoopResult:
        """
        Execute the edit-test loop.

        Args:
            task: The coding task description.
            files: List of file paths to operate on.
            config: Agent config dict (for creating provider).
            max_iterations: Maximum edit-test cycles.

        Returns:
            LoopResult with all iteration details.
        """
        config = config or self._read_config()
        test_command = self._detect_test_command(files)
        iterations: List[IterationResult] = []
        total_tokens = 0
        prev_test_output = ""

        # Save initial checkpoint
        self._checkpoint({
            "task": task,
            "files": files,
            "iteration": 0,
            "max_iterations": max_iterations,
            "test_command": test_command,
            "iterations": [],
            "status": "running",
            "started_at": datetime.utcnow().isoformat(),
        })

        for i in range(1, max_iterations + 1):
            result = self._iterate(
                task=task,
                files=files,
                config=config,
                prev_test_output=prev_test_output,
                iteration=i,
            )
            iterations.append(result)
            total_tokens += result.tokens_used

            # Checkpoint after each iteration
            self._checkpoint({
                "task": task,
                "files": files,
                "iteration": i,
                "max_iterations": max_iterations,
                "test_command": test_command,
                "iterations": [
                    {
                        "number": r.iteration,
                        "edits": r.edits_applied,
                        "test_passed": r.test_passed,
                        "test_output": r.test_output[:500],
                        "tokens": r.tokens_used,
                    }
                    for r in iterations
                ],
                "status": "completed" if result.test_passed else "running",
                "updated_at": datetime.utcnow().isoformat(),
            })

            if result.test_passed:
                break

            prev_test_output = result.test_output

        success = iterations[-1].test_passed if iterations else False

        # Build final output summary
        final_output = self._build_summary(task, iterations, test_command, success)

        # Mark completed
        self._checkpoint({
            "task": task,
            "files": files,
            "iteration": len(iterations),
            "max_iterations": max_iterations,
            "test_command": test_command,
            "iterations": [
                {
                    "number": r.iteration,
                    "edits": r.edits_applied,
                    "test_passed": r.test_passed,
                    "test_output": r.test_output[:500],
                    "tokens": r.tokens_used,
                }
                for r in iterations
            ],
            "status": "completed" if success else "failed",
            "total_tokens": total_tokens,
            "completed_at": datetime.utcnow().isoformat(),
        })

        return LoopResult(
            task=task,
            iterations=iterations,
            total_tokens=total_tokens,
            success=success,
            final_output=final_output,
        )

    def resume(self, config: Optional[Dict[str, Any]] = None) -> Optional[LoopResult]:
        """Resume an interrupted coding loop from checkpoint."""
        state = self._load_checkpoint()
        if not state or state.get("status") not in ("running",):
            return None

        config = config or self._read_config()
        task = state["task"]
        files = state["files"]
        max_iterations = state.get("max_iterations", 5)
        current_iteration = state.get("iteration", 0)
        test_command = state.get("test_command")

        # Rebuild iteration history
        iterations: List[IterationResult] = []
        total_tokens = 0
        for it in state.get("iterations", []):
            ir = IterationResult(
                iteration=it["number"],
                edits_applied=it.get("edits", []),
                test_command=test_command,
                test_passed=it.get("test_passed", False),
                test_output=it.get("test_output", ""),
                tokens_used=it.get("tokens", 0),
            )
            iterations.append(ir)
            total_tokens += ir.tokens_used

        # Get last test output for context
        prev_test_output = ""
        if iterations:
            prev_test_output = iterations[-1].test_output

        # Continue from where we left off
        for i in range(current_iteration + 1, max_iterations + 1):
            result = self._iterate(
                task=task,
                files=files,
                config=config,
                prev_test_output=prev_test_output,
                iteration=i,
            )
            iterations.append(result)
            total_tokens += result.tokens_used

            self._checkpoint({
                "task": task,
                "files": files,
                "iteration": i,
                "max_iterations": max_iterations,
                "test_command": test_command,
                "iterations": [
                    {
                        "number": r.iteration,
                        "edits": r.edits_applied,
                        "test_passed": r.test_passed,
                        "test_output": r.test_output[:500],
                        "tokens": r.tokens_used,
                    }
                    for r in iterations
                ],
                "status": "completed" if result.test_passed else "running",
                "updated_at": datetime.utcnow().isoformat(),
            })

            if result.test_passed:
                break
            prev_test_output = result.test_output

        success = iterations[-1].test_passed if iterations else False
        final_output = self._build_summary(task, iterations, test_command, success)

        return LoopResult(
            task=task,
            iterations=iterations,
            total_tokens=total_tokens,
            success=success,
            final_output=final_output,
        )

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current loop status from checkpoint."""
        return self._load_checkpoint()

    def reset(self) -> bool:
        """Clear loop checkpoint."""
        state_file = self.loop_dir / "state.yaml"
        if state_file.exists():
            state_file.unlink()
            return True
        return False

    # ------------------------------------------------------------------
    # Single iteration
    # ------------------------------------------------------------------

    def _iterate(
        self,
        task: str,
        files: List[str],
        config: Dict[str, Any],
        prev_test_output: str,
        iteration: int,
    ) -> IterationResult:
        """Execute a single edit-test iteration."""
        # 1. Read current file contents
        file_contents = self._read_files(files)

        # 2. Build minimal prompt
        prompt = self._build_prompt(task, file_contents, prev_test_output, iteration)

        # 3. Ask LLM for edits
        provider = self._create_provider(config)
        response = provider.complete(prompt=prompt)

        # 4. Parse edits from response
        edits = self._parse_edits(response.content)

        # 5. Apply edits to filesystem
        applied = self._apply_edits(edits)

        # 6. Detect and run tests
        test_command = self._detect_test_command(files)
        test_passed = False
        test_output = ""

        if test_command:
            test_passed, test_output = self._run_tests(test_command)
        else:
            # No test command found — treat as single-pass success
            test_passed = True
            test_output = "No test framework detected. Edits applied."

        return IterationResult(
            iteration=iteration,
            edits_applied=applied,
            test_command=test_command,
            test_passed=test_passed,
            test_output=test_output,
            tokens_used=response.token_usage,
        )

    # ------------------------------------------------------------------
    # Prompt building
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        task: str,
        file_contents: Dict[str, str],
        test_output: str,
        iteration: int,
    ) -> str:
        """Build a minimal, token-efficient prompt."""
        parts = []

        parts.append(
            "You are a coding assistant. Your job is to modify code files "
            "to accomplish the task. Output ONLY edit blocks in the exact "
            "format shown below. Do not include explanations outside edit blocks."
        )

        parts.append(f"\n## Task\n{task}")

        # Current file contents
        parts.append("\n## Current Files")
        for path, content in file_contents.items():
            # Truncate very large files
            if len(content) > 8000:
                lines = content.split("\n")
                content = "\n".join(lines[:150] + ["...", f"[{len(lines) - 200} lines omitted]"] + lines[-50:])
            parts.append(f"\n### {path}\n```\n{content}\n```")

        # Previous test output (if not first iteration)
        if test_output and iteration > 1:
            # Truncate to keep tokens low
            if len(test_output) > 2000:
                test_output = test_output[:1000] + "\n...\n" + test_output[-1000:]
            parts.append(f"\n## Test Output (iteration {iteration - 1} — FAILED)\n```\n{test_output}\n```")
            parts.append(
                f"\nThis is iteration {iteration}. Fix the errors shown above."
            )

        # Edit format instructions
        parts.append("""
## Edit Format

To modify an existing file, use:
```
<<<EDIT file="path/to/file.py">>>
<<<OLD>>>
exact lines to replace
<<<NEW>>>
replacement lines
<<<END>>>
```

To create a new file, use:
```
<<<CREATE file="path/to/new_file.py">>>
file content here
<<<END>>>
```

Output ONLY edit blocks. Multiple edits per file are allowed.""")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Edit parsing
    # ------------------------------------------------------------------

    def _parse_edits(self, response: str) -> List[Edit]:
        """Parse <<<EDIT>>> and <<<CREATE>>> blocks from LLM response."""
        edits = []

        # Parse EDIT blocks
        edit_pattern = re.compile(
            r'<<<EDIT\s+file="([^"]+)">>>\s*'
            r'<<<OLD>>>\s*\n(.*?)\n\s*<<<NEW>>>\s*\n(.*?)\n\s*<<<END>>>',
            re.DOTALL,
        )
        for match in edit_pattern.finditer(response):
            edits.append(Edit(
                file_path=match.group(1),
                old_content=match.group(2),
                new_content=match.group(3),
                is_create=False,
            ))

        # Parse CREATE blocks
        create_pattern = re.compile(
            r'<<<CREATE\s+file="([^"]+)">>>\s*\n(.*?)\n\s*<<<END>>>',
            re.DOTALL,
        )
        for match in create_pattern.finditer(response):
            edits.append(Edit(
                file_path=match.group(1),
                old_content="",
                new_content=match.group(2),
                is_create=True,
            ))

        return edits

    # ------------------------------------------------------------------
    # Edit application
    # ------------------------------------------------------------------

    def _apply_edits(self, edits: List[Edit]) -> List[Dict[str, Any]]:
        """Apply edits to the filesystem. Returns list of applied edit info."""
        applied = []

        for edit in edits:
            path = self.workspace / edit.file_path
            try:
                if edit.is_create:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(edit.new_content)
                    applied.append({
                        "file": edit.file_path,
                        "action": "create",
                        "applied": True,
                    })
                else:
                    if not path.exists():
                        applied.append({
                            "file": edit.file_path,
                            "action": "edit",
                            "applied": False,
                            "error": "file not found",
                        })
                        continue

                    content = path.read_text()
                    if edit.old_content in content:
                        new_content = content.replace(edit.old_content, edit.new_content, 1)
                        path.write_text(new_content)
                        applied.append({
                            "file": edit.file_path,
                            "action": "edit",
                            "applied": True,
                        })
                    else:
                        applied.append({
                            "file": edit.file_path,
                            "action": "edit",
                            "applied": False,
                            "error": "old content not found",
                        })
            except Exception as e:
                applied.append({
                    "file": edit.file_path,
                    "action": "create" if edit.is_create else "edit",
                    "applied": False,
                    "error": str(e),
                })

        return applied

    # ------------------------------------------------------------------
    # Test detection and execution
    # ------------------------------------------------------------------

    def _detect_test_command(self, files: List[str]) -> Optional[str]:
        """Auto-detect the test command for this project."""
        ws = self.workspace

        # 1. pytest
        if (ws / "pytest.ini").exists():
            return "python -m pytest"
        if (ws / "pyproject.toml").exists():
            try:
                content = (ws / "pyproject.toml").read_text()
                if "[tool.pytest" in content:
                    return "python -m pytest"
            except Exception:
                pass
        if (ws / "setup.cfg").exists():
            try:
                content = (ws / "setup.cfg").read_text()
                if "[tool:pytest]" in content:
                    return "python -m pytest"
            except Exception:
                pass

        # 2. Node.js
        if (ws / "package.json").exists():
            try:
                import json
                pkg = json.loads((ws / "package.json").read_text())
                if "test" in pkg.get("scripts", {}):
                    return "npm test"
            except Exception:
                pass

        # 3. Vitest
        for vite_cfg in ws.glob("vitest.config.*"):
            return "npx vitest run"

        # 4. Go
        if (ws / "go.mod").exists():
            return "go test ./..."

        # 5. Rust
        if (ws / "Cargo.toml").exists():
            return "cargo test"

        # 6. Makefile with test target
        if (ws / "Makefile").exists():
            try:
                content = (ws / "Makefile").read_text()
                if re.search(r'^test\s*:', content, re.MULTILINE):
                    return "make test"
            except Exception:
                pass

        # 7. Fallback: pytest if any .py files in the target list
        if any(f.endswith(".py") for f in files):
            return "python -m pytest"

        return None

    def _run_tests(self, test_command: str, timeout: int = 60) -> Tuple[bool, str]:
        """Run tests via subprocess. Returns (passed, output)."""
        try:
            result = subprocess.run(
                test_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.workspace),
            )
            output = result.stdout + result.stderr
            # Truncate to keep checkpoint size reasonable
            if len(output) > 5000:
                output = output[:2500] + "\n...\n" + output[-2500:]
            return result.returncode == 0, output
        except subprocess.TimeoutExpired:
            return False, f"Tests timed out after {timeout}s"
        except Exception as e:
            return False, f"Test execution error: {e}"

    # ------------------------------------------------------------------
    # Checkpoint persistence
    # ------------------------------------------------------------------

    def _checkpoint(self, state: Dict[str, Any]) -> None:
        """Save loop state to .geekcode/loop/state.yaml."""
        state_file = self.loop_dir / "state.yaml"
        with open(state_file, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    def _load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load loop state from .geekcode/loop/state.yaml."""
        state_file = self.loop_dir / "state.yaml"
        if not state_file.exists():
            return None
        try:
            with open(state_file) as f:
                return yaml.safe_load(f) or None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read_files(self, files: List[str]) -> Dict[str, str]:
        """Read file contents from the workspace."""
        contents = {}
        for file_path in files:
            path = self.workspace / file_path
            if path.exists():
                try:
                    contents[file_path] = path.read_text(errors="ignore")
                except Exception:
                    contents[file_path] = f"[Error reading {file_path}]"
        return contents

    def _read_config(self) -> Dict[str, Any]:
        """Read config from .geekcode/config.yaml."""
        config_file = self.geekcode_dir / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _create_provider(self, config: Dict[str, Any]):
        """Create an LLM provider from config."""
        from geekcode.providers.base import ProviderFactory

        model = config.get("model", "claude-sonnet-4-5")

        class ConfigWrapper:
            def __init__(self, cfg):
                self._cfg = cfg

            def get_api_key(self, provider):
                api = self._cfg.get("api", {})
                key = api.get(provider)
                if key:
                    return key
                env_map = {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "google": "GOOGLE_API_KEY",
                    "groq": "GROQ_API_KEY",
                    "together": "TOGETHER_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                }
                return os.environ.get(env_map.get(provider, ""))

            def get_provider_config(self, provider):
                return None

            @property
            def merged(self):
                return self

            @property
            def agent(self):
                class AgentConfig:
                    max_tokens = 4096
                    temperature = 0.3  # Lower temp for code edits
                    timeout = 120
                return AgentConfig()

        return ProviderFactory.create(model, ConfigWrapper(config))

    def _build_summary(
        self,
        task: str,
        iterations: List[IterationResult],
        test_command: Optional[str],
        success: bool,
    ) -> str:
        """Build a human-readable summary of the loop execution."""
        parts = []

        if success:
            parts.append(f"**Task completed** in {len(iterations)} iteration(s).")
        else:
            parts.append(
                f"**Task incomplete** after {len(iterations)} iteration(s). "
                "Tests still failing."
            )

        parts.append("")

        total_edits = sum(len(it.edits_applied) for it in iterations)
        total_tokens = sum(it.tokens_used for it in iterations)
        parts.append(f"- **Edits applied**: {total_edits}")
        parts.append(f"- **Tokens used**: {total_tokens:,}")
        if test_command:
            parts.append(f"- **Test command**: `{test_command}`")

        parts.append("")

        for it in iterations:
            status = "PASS" if it.test_passed else "FAIL"
            parts.append(
                f"**Iteration {it.iteration}**: {status} "
                f"({len(it.edits_applied)} edits, {it.tokens_used:,} tokens)"
            )

        # Show last test output if failed
        if not success and iterations:
            last = iterations[-1]
            if last.test_output:
                parts.append(f"\n**Last test output:**\n```\n{last.test_output[:1000]}\n```")

        return "\n".join(parts)
