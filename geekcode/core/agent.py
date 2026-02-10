"""
GeekCode Agent - Fully filesystem-driven, zero memory.

Every task execution:
1. Read state from files
2. Read conversation context from files
3. Execute task
4. Write checkpoint to files
5. Return result (no state kept in memory)
"""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class TaskResult:
    """Result from a task execution."""
    output: str
    task_id: str
    model: str
    tokens_used: int = 0
    tokens_saved: int = 0
    cached: bool = False
    completed: bool = True
    error: Optional[str] = None


class Agent:
    """
    Fully filesystem-driven agent.

    NO memory between task executions.
    Every run():
    - Reads state from .geekcode/state.yaml
    - Reads conversation from .geekcode/conversation.yaml
    - Executes task
    - Writes checkpoint to files
    - Returns result

    The Agent class itself holds no state.
    """

    def __init__(self, workspace: Optional[Path] = None):
        """
        Initialize agent for a workspace.

        Note: This only stores the workspace path.
        All state is read from files on each run().
        """
        self.workspace = self._find_workspace(workspace)
        self.geekcode_dir = self.workspace / ".geekcode"

    def _find_workspace(self, workspace: Optional[Path]) -> Path:
        """Find workspace by looking for .geekcode/ directory."""
        if workspace:
            return Path(workspace)

        current = Path.cwd()
        while current != current.parent:
            if (current / ".geekcode").exists():
                return current
            current = current.parent

        return Path.cwd()

    def run(self, task: str, files: Optional[List[str]] = None) -> TaskResult:
        """
        Execute a task. Fully filesystem-driven.

        Every call:
        1. Load state from files
        2. Load conversation from files
        3. Check cache
        4. Build context from files
        5. Execute
        6. Save all state to files
        7. Return result (nothing kept in memory)
        """
        # === READ PHASE: Load everything from files ===
        state = self._read_state()
        config = self._read_config()
        conversation = self._read_conversation()

        # Generate task ID
        task_id = self._generate_task_id(task, files, conversation)

        # === CACHE CHECK: Read from cache files ===
        cached = self._read_cache(task_id)
        if cached:
            # Write to history file
            self._write_history(task, cached, cached=True)
            return TaskResult(
                output=cached,
                task_id=task_id,
                model=config.get("model", "unknown"),
                tokens_used=0,
                tokens_saved=self._estimate_tokens(task + cached),
                cached=True,
            )

        # === CODING LOOP: If files provided and task looks like coding ===
        from geekcode.core.coding_loop import CodingLoop, is_coding_task

        if files and is_coding_task(task):
            loop = CodingLoop(self.workspace, self.geekcode_dir)
            loop_result = loop.run(task, files, config=config, max_iterations=5)
            # Write history
            self._write_history(task, loop_result.final_output, cached=False)
            return TaskResult(
                output=loop_result.final_output,
                task_id=task_id,
                model=config.get("model", "unknown"),
                tokens_used=loop_result.total_tokens,
                completed=loop_result.success,
            )

        # === CONTEXT PHASE: Read from context files ===
        context = self._build_context_from_files(task, files)

        # === CHECKPOINT: Write pre-execution state ===
        state["status"] = "running"
        state["current_task"] = task
        state["task_id"] = task_id
        state["started_at"] = datetime.utcnow().isoformat()
        self._write_state(state)

        # === EXECUTE PHASE ===
        try:
            # Build prompt with conversation context from files
            prompt = self._build_prompt(task, context, conversation)

            # Create provider (stateless - just uses config)
            provider = self._create_provider(config)

            # Execute
            response = provider.complete(prompt=prompt)

            # === WRITE PHASE: Save everything to files ===

            # Update conversation file
            conversation.append({"role": "user", "content": task})
            conversation.append({"role": "assistant", "content": response.content})
            self._write_conversation(conversation)

            # Write to cache file
            self._write_cache(task_id, response.content)

            # Update state file
            state["status"] = "completed"
            state["completed_at"] = datetime.utcnow().isoformat()
            state["last_result"] = response.content[:500]
            state["last_task_id"] = task_id
            self._write_state(state)

            # Write to history file
            self._write_history(task, response.content, cached=False)

            return TaskResult(
                output=response.content,
                task_id=task_id,
                model=response.model,
                tokens_used=response.token_usage,
                completed=True,
            )

        except KeyboardInterrupt:
            # === INTERRUPTED: Save paused state and re-raise ===
            state["status"] = "paused"
            state["paused_at"] = datetime.utcnow().isoformat()
            self._write_state(state)
            raise

        except Exception as e:
            # === ERROR: Write error state to file ===
            state["status"] = "error"
            state["error"] = str(e)
            state["error_at"] = datetime.utcnow().isoformat()
            self._write_state(state)

            return TaskResult(
                output="",
                task_id=task_id,
                model=config.get("model", "unknown"),
                completed=False,
                error=str(e),
            )

    # === FILE READ OPERATIONS ===

    def _read_state(self) -> Dict[str, Any]:
        """Read state from .geekcode/state.yaml"""
        state_file = self.geekcode_dir / "state.yaml"
        if state_file.exists():
            with open(state_file) as f:
                return yaml.safe_load(f) or {}
        return {"status": "idle"}

    def _read_config(self) -> Dict[str, Any]:
        """Read config from project-local .geekcode/config.yaml only.

        No global config — all preferences are per-project.
        API keys come from environment variables, never from files.
        """
        config = {}
        local_file = self.geekcode_dir / "config.yaml"
        if local_file.exists():
            with open(local_file) as f:
                config = yaml.safe_load(f) or {}
        return config

    def _read_conversation(self) -> List[Dict[str, str]]:
        """Read conversation history from .geekcode/conversation.yaml"""
        conv_file = self.geekcode_dir / "conversation.yaml"
        if conv_file.exists():
            with open(conv_file) as f:
                return yaml.safe_load(f) or []
        return []

    def _read_cache(self, task_id: str) -> Optional[str]:
        """Read cached response from .geekcode/cache/responses/"""
        cache_file = self.geekcode_dir / "cache" / "responses" / f"{task_id}.yaml"
        if not cache_file.exists():
            return None

        with open(cache_file) as f:
            data = yaml.safe_load(f) or {}

        # Check TTL
        cached_at = data.get("cached_at", "")
        if cached_at:
            from datetime import timedelta
            cache_time = datetime.fromisoformat(cached_at)
            if datetime.utcnow() - cache_time > timedelta(hours=24):
                cache_file.unlink()
                return None

        # Update hit counter
        self._increment_cache_hits()

        return data.get("response")

    # === FILE WRITE OPERATIONS ===

    def _write_state(self, state: Dict[str, Any]) -> None:
        """Write state to .geekcode/state.yaml"""
        state_file = self.geekcode_dir / "state.yaml"
        with open(state_file, "w") as f:
            yaml.dump(state, f, default_flow_style=False)

    def _write_conversation(self, conversation: List[Dict[str, str]]) -> None:
        """Write conversation to .geekcode/conversation.yaml"""
        # Keep only last 20 messages to limit context size
        conversation = conversation[-20:]
        conv_file = self.geekcode_dir / "conversation.yaml"
        with open(conv_file, "w") as f:
            yaml.dump(conversation, f, default_flow_style=False)

    def _write_cache(self, task_id: str, response: str) -> None:
        """Write response to cache file."""
        cache_dir = self.geekcode_dir / "cache" / "responses"
        cache_dir.mkdir(parents=True, exist_ok=True)

        cache_file = cache_dir / f"{task_id}.yaml"
        with open(cache_file, "w") as f:
            yaml.dump({
                "cached_at": datetime.utcnow().isoformat(),
                "response": response,
            }, f, default_flow_style=False)

    def _write_history(self, task: str, response: str, cached: bool) -> None:
        """Append to daily history file."""
        history_dir = self.geekcode_dir / "history"
        history_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.utcnow().strftime("%Y-%m-%d")
        history_file = history_dir / f"{today}.yaml"

        history = []
        if history_file.exists():
            with open(history_file) as f:
                history = yaml.safe_load(f) or []

        history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "task": task[:200],
            "response_preview": response[:200],
            "cached": cached,
        })

        with open(history_file, "w") as f:
            yaml.dump(history, f, default_flow_style=False)

    def _increment_cache_hits(self) -> None:
        """Increment cache hit counter in meta file."""
        meta_file = self.geekcode_dir / "cache" / "meta.yaml"
        meta = {}
        if meta_file.exists():
            with open(meta_file) as f:
                meta = yaml.safe_load(f) or {}

        meta["hits"] = meta.get("hits", 0) + 1
        meta["tokens_saved"] = meta.get("tokens_saved", 0) + 500  # Estimate

        with open(meta_file, "w") as f:
            yaml.dump(meta, f, default_flow_style=False)

    # === CONTEXT BUILDING ===

    def _build_context_from_files(
        self,
        task: str,
        files: Optional[List[str]],
    ) -> str:
        """Build context by reading from indexed files."""
        context_parts = []

        if files:
            for file_path in files:
                path = Path(file_path)
                if path.exists():
                    content = path.read_text(errors="ignore")
                    # Summarize large files
                    if len(content) > 5000:
                        content = self._summarize_content(content)
                    context_parts.append(f"## {file_path}\n{content}")
        else:
            # Search indexed chunks
            chunks = self._search_indexed_chunks(task)
            for chunk in chunks[:3]:
                context_parts.append(f"## {chunk['source']}\n{chunk['content']}")

        return "\n\n".join(context_parts)

    def _search_indexed_chunks(self, query: str) -> List[Dict[str, str]]:
        """Search chunks in .geekcode/context/chunks/"""
        chunks_dir = self.geekcode_dir / "context" / "chunks"
        if not chunks_dir.exists():
            return []

        query_words = set(query.lower().split())
        results = []

        for chunk_file in chunks_dir.glob("*.txt"):
            content = chunk_file.read_text()
            content_words = set(content.lower().split())
            score = len(query_words & content_words)

            if score > 0:
                # Read source from index
                index_file = self.geekcode_dir / "context" / "index.yaml"
                source = chunk_file.stem.split("_")[0]

                if index_file.exists():
                    with open(index_file) as f:
                        index = yaml.safe_load(f) or {}
                    for path, info in index.items():
                        if info.get("hash", "")[:8] == source[:8]:
                            source = path
                            break

                results.append({
                    "content": content,
                    "source": source,
                    "score": score,
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:5]

    def _build_prompt(
        self,
        task: str,
        context: str,
        conversation: List[Dict[str, str]],
    ) -> str:
        """Build prompt with conversation history from files."""
        parts = []

        # Add recent conversation (loaded from file)
        if conversation:
            parts.append("## Previous Conversation")
            for msg in conversation[-6:]:  # Last 3 exchanges
                role = "User" if msg["role"] == "user" else "Assistant"
                parts.append(f"{role}: {msg['content'][:500]}")

        # Add context
        if context:
            parts.append(f"\n## Context\n{context}")

        # Add available tools (lean names only — MCPorter)
        try:
            from geekcode.mcporter.registry import ToolRegistry
            registry = ToolRegistry(self.geekcode_dir)
            tools_fragment = registry.build_prompt_fragment()
            if tools_fragment:
                parts.append(f"\n## Available Tools\n{tools_fragment}")
        except Exception:
            pass  # MCPorter not configured or no tools available

        # Add task
        parts.append(f"\n## Current Task\n{task}")
        parts.append("\nRespond concisely and directly.")

        return "\n".join(parts)

    # === UTILITIES ===

    def _generate_task_id(
        self,
        task: str,
        files: Optional[List[str]],
        conversation: List[Dict[str, str]],
    ) -> str:
        """Generate task ID based on content hash."""
        content = task

        # Include file mtimes
        if files:
            for f in sorted(files):
                path = Path(f)
                if path.exists():
                    content += f + str(path.stat().st_mtime)

        # Include conversation context hash
        if conversation:
            conv_str = str(conversation[-4:])  # Last 2 exchanges
            content += conv_str

        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _estimate_tokens(self, text: str) -> int:
        """Estimate tokens (4 chars per token)."""
        return len(text) // 4

    def _summarize_content(self, content: str) -> str:
        """Summarize large content."""
        lines = content.split("\n")
        if len(lines) <= 30:
            return content

        return "\n".join(
            lines[:15] +
            ["...", f"[{len(lines) - 30} lines omitted]", "..."] +
            lines[-15:]
        )

    def _merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge(result[key], value)
            else:
                result[key] = value
        return result

    def _create_provider(self, config: Dict[str, Any]):
        """Create provider (stateless - uses config). Falls back to other providers on ImportError."""
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
                    temperature = 0.7
                return AgentConfig()

        wrapper = ConfigWrapper(config)

        # Try the configured model first, fall back to others on ImportError
        try:
            return ProviderFactory.create(model, wrapper)
        except ImportError:
            # Provider package missing — try other providers that have API keys set
            fallback_models = [
                ("ANTHROPIC_API_KEY", "claude-sonnet-4-5"),
                ("OPENAI_API_KEY", "gpt-4o"),
                ("GOOGLE_API_KEY", "gemini-2.0-flash"),
            ]
            for env_var, fallback_model in fallback_models:
                if fallback_model == model:
                    continue  # Already failed
                if os.environ.get(env_var):
                    try:
                        return ProviderFactory.create(fallback_model, wrapper)
                    except ImportError:
                        continue
            # Nothing worked — raise original error with helpful message
            raise ImportError(
                f"Could not load provider for '{model}'. "
                f"If using the binary, please report this issue. "
                f"If using pip, install with: pip install geekcode[openai,anthropic,google]"
            )

    def clear_conversation(self) -> None:
        """Clear conversation file."""
        conv_file = self.geekcode_dir / "conversation.yaml"
        if conv_file.exists():
            conv_file.unlink()

    def clear_cache(self) -> None:
        """Clear cache files."""
        cache_dir = self.geekcode_dir / "cache" / "responses"
        if cache_dir.exists():
            for f in cache_dir.glob("*.yaml"):
                f.unlink()
