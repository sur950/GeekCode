"""
GeekCode Context Engine - Filesystem-based context management.

Manages:
- File indexing with hashes (detect changes)
- Chunking and embeddings
- Incremental updates (only process changed files)
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class Chunk:
    """A chunk of content from a file."""
    content: str
    source: str
    index: int
    score: float = 0.0


@dataclass
class FileIndex:
    """Index entry for a file."""
    path: str
    hash: str
    size: int
    chunks: int
    indexed_at: str


class ContextEngine:
    """
    Filesystem-based context management.

    All state persists in:
    - context/index.yaml - file hashes and metadata
    - context/chunks/ - chunked content
    - context/embeddings.db - vector store
    """

    def __init__(self, context_dir: Path):
        self.context_dir = Path(context_dir)
        self.context_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self.context_dir / "index.yaml"
        self.chunks_dir = self.context_dir / "chunks"
        self.chunks_dir.mkdir(exist_ok=True)

    def add_file(self, file_path: str) -> bool:
        """
        Index a file if it has changed.

        Returns True if file was (re)indexed, False if unchanged.
        """
        path = Path(file_path)
        if not path.exists():
            return False

        # Calculate hash
        content = path.read_text(errors="ignore")
        file_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Check if already indexed with same hash
        index = self._load_index()
        existing = index.get(str(path))
        if existing and existing.get("hash") == file_hash:
            return False  # Unchanged

        # Chunk the file
        chunks = self._chunk_content(content, str(path))

        # Save chunks
        for i, chunk in enumerate(chunks):
            chunk_file = self.chunks_dir / f"{file_hash}_{i}.txt"
            chunk_file.write_text(chunk)

        # Update index
        from datetime import datetime
        index[str(path)] = {
            "hash": file_hash,
            "size": len(content),
            "chunks": len(chunks),
            "indexed_at": datetime.utcnow().isoformat(),
        }
        self._save_index(index)

        return True

    def get_file_content(self, file_path: str) -> Optional[str]:
        """Get content of an indexed file."""
        path = Path(file_path)
        if path.exists():
            return path.read_text(errors="ignore")
        return None

    def search(self, query: str, top_k: int = 5) -> List[Chunk]:
        """
        Search indexed content for relevant chunks.

        Simple keyword matching for now (embedding search requires more setup).
        """
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())

        for chunk_file in self.chunks_dir.glob("*.txt"):
            content = chunk_file.read_text()
            content_lower = content.lower()

            # Score by keyword overlap
            content_words = set(content_lower.split())
            overlap = len(query_words & content_words)

            if overlap > 0:
                # Extract source from filename
                parts = chunk_file.stem.split("_")
                file_hash = parts[0]
                chunk_idx = int(parts[1]) if len(parts) > 1 else 0

                # Find source file from index
                source = self._find_source_by_hash(file_hash)

                results.append(Chunk(
                    content=content,
                    source=source or chunk_file.name,
                    index=chunk_idx,
                    score=overlap / len(query_words),
                ))

        # Sort by score and return top_k
        results.sort(key=lambda c: c.score, reverse=True)
        return results[:top_k]

    def get_changed_files(self) -> List[str]:
        """Get list of files that changed since last index."""
        index = self._load_index()
        changed = []

        for file_path, info in index.items():
            path = Path(file_path)
            if not path.exists():
                continue

            content = path.read_text(errors="ignore")
            current_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

            if current_hash != info.get("hash"):
                changed.append(file_path)

        return changed

    def index_workspace(self, workspace: Path, max_files: int = 500) -> int:
        """Index workspace files for chunk-based search.

        Reuses _walk_project_files() from workspace_query to get eligible files.
        Skips files already indexed with the same hash (incremental).

        Returns count of files indexed (new or re-indexed).
        """
        from geekcode.core.workspace_query import _walk_project_files

        files = _walk_project_files(workspace, max_files=max_files)
        indexed_count = 0

        for file_path in files:
            try:
                if self.add_file(str(file_path)):
                    indexed_count += 1
            except Exception:
                continue

        return indexed_count

    def clear(self) -> None:
        """Clear all indexed content."""
        # Clear chunks
        for chunk_file in self.chunks_dir.glob("*.txt"):
            chunk_file.unlink()

        # Clear index
        if self._index_path.exists():
            self._index_path.unlink()

    def _chunk_content(self, content: str, source: str) -> List[str]:
        """Split content into chunks."""
        # Simple chunking by paragraphs/sections
        chunks = []
        current_chunk = []
        current_size = 0
        max_chunk_size = 1000  # characters

        lines = content.split("\n")
        for line in lines:
            current_chunk.append(line)
            current_size += len(line)

            # Break on paragraph boundaries or size limit
            if current_size >= max_chunk_size or (line.strip() == "" and current_size > 200):
                chunk_text = "\n".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)
                current_chunk = []
                current_size = 0

        # Don't forget last chunk
        if current_chunk:
            chunk_text = "\n".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks

    def _load_index(self) -> Dict[str, Any]:
        """Load file index."""
        if self._index_path.exists():
            with open(self._index_path) as f:
                return yaml.safe_load(f) or {}
        return {}

    def _save_index(self, index: Dict[str, Any]) -> None:
        """Save file index."""
        with open(self._index_path, "w") as f:
            yaml.dump(index, f, default_flow_style=False)

    def _find_source_by_hash(self, file_hash: str) -> Optional[str]:
        """Find source file path by hash."""
        index = self._load_index()
        for path, info in index.items():
            if info.get("hash") == file_hash:
                return path
        return None
