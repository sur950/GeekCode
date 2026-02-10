"""
GeekCode Cache Engine - Token-saving response cache.

Caches:
- LLM responses by task hash
- File summaries
- Embedding results

All stored in .geekcode/cache/
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class CacheEngine:
    """
    Filesystem-based cache for token optimization.

    Cache structure:
    - cache/responses/   - LLM response cache
    - cache/summaries/   - File summary cache
    - cache/meta.yaml    - Cache metadata and stats
    """

    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.responses_dir = self.cache_dir / "responses"
        self.responses_dir.mkdir(exist_ok=True)
        self.summaries_dir = self.cache_dir / "summaries"
        self.summaries_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def get(self, task_id: str) -> Optional[str]:
        """
        Get cached response for a task.

        Returns None if not cached or expired.
        """
        cache_file = self.responses_dir / f"{task_id}.yaml"
        if not cache_file.exists():
            return None

        with open(cache_file) as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Check expiry
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        if datetime.utcnow() - cached_at > self.ttl:
            cache_file.unlink()
            return None

        # Update stats
        self._record_hit(task_id)

        return data.get("response")

    def set(self, task_id: str, response: str) -> None:
        """Cache a response."""
        cache_file = self.responses_dir / f"{task_id}.yaml"

        data = {
            "cached_at": datetime.utcnow().isoformat(),
            "response": response,
            "tokens_estimate": len(response) // 4,
        }

        with open(cache_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        self._record_set(task_id, len(response))

    def get_summary(self, file_path: str) -> Optional[str]:
        """Get cached file summary."""
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        cache_file = self.summaries_dir / f"{file_hash}.yaml"

        if not cache_file.exists():
            return None

        with open(cache_file) as f:
            data = yaml.safe_load(f)

        if not data:
            return None

        # Check if source file changed
        source = Path(file_path)
        if source.exists():
            current_mtime = source.stat().st_mtime
            cached_mtime = data.get("source_mtime", 0)
            if current_mtime > cached_mtime:
                cache_file.unlink()
                return None

        return data.get("summary")

    def set_summary(self, file_path: str, summary: str) -> None:
        """Cache a file summary."""
        file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:16]
        cache_file = self.summaries_dir / f"{file_hash}.yaml"

        source = Path(file_path)
        mtime = source.stat().st_mtime if source.exists() else 0

        data = {
            "source_path": file_path,
            "source_mtime": mtime,
            "cached_at": datetime.utcnow().isoformat(),
            "summary": summary,
        }

        with open(cache_file, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def clear(self, older_than_hours: Optional[int] = None) -> int:
        """
        Clear cache entries.

        Args:
            older_than_hours: Only clear entries older than this.
                            If None, clear all.

        Returns:
            Number of entries cleared.
        """
        cleared = 0
        cutoff = None
        if older_than_hours:
            cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)

        for cache_file in self.responses_dir.glob("*.yaml"):
            should_clear = True

            if cutoff:
                with open(cache_file) as f:
                    data = yaml.safe_load(f) or {}
                cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
                should_clear = cached_at < cutoff

            if should_clear:
                cache_file.unlink()
                cleared += 1

        return cleared

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        meta_file = self.cache_dir / "meta.yaml"
        if meta_file.exists():
            with open(meta_file) as f:
                meta = yaml.safe_load(f) or {}
        else:
            meta = {}

        # Count current cache entries
        response_count = len(list(self.responses_dir.glob("*.yaml")))
        summary_count = len(list(self.summaries_dir.glob("*.yaml")))

        # Calculate size
        total_size = 0
        for f in self.cache_dir.rglob("*.yaml"):
            total_size += f.stat().st_size

        return {
            "response_cache_entries": response_count,
            "summary_cache_entries": summary_count,
            "total_size_kb": total_size / 1024,
            "hits": meta.get("hits", 0),
            "sets": meta.get("sets", 0),
            "tokens_saved_estimate": meta.get("tokens_saved", 0),
        }

    def _record_hit(self, task_id: str) -> None:
        """Record a cache hit."""
        meta = self._load_meta()
        meta["hits"] = meta.get("hits", 0) + 1

        # Estimate tokens saved (rough: task + response average ~500 tokens)
        meta["tokens_saved"] = meta.get("tokens_saved", 0) + 500

        self._save_meta(meta)

    def _record_set(self, task_id: str, response_len: int) -> None:
        """Record a cache set."""
        meta = self._load_meta()
        meta["sets"] = meta.get("sets", 0) + 1
        self._save_meta(meta)

    def _load_meta(self) -> Dict[str, Any]:
        """Load cache metadata."""
        meta_file = self.cache_dir / "meta.yaml"
        if meta_file.exists():
            with open(meta_file) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _save_meta(self, meta: Dict[str, Any]) -> None:
        """Save cache metadata."""
        meta_file = self.cache_dir / "meta.yaml"
        with open(meta_file, "w") as f:
            yaml.dump(meta, f, default_flow_style=False)
