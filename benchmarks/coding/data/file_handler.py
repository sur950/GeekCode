# Synchronous file handler - needs async migration
# This is sample input for Task 3: Async Migration

import os
import json
from typing import Any, List, Optional


class FileHandler:
    """Synchronous file operations handler."""

    def __init__(self, base_path: str = "."):
        self.base_path = os.path.abspath(base_path)

    def read_text(self, filepath: str) -> str:
        """Read a text file."""
        full_path = self._get_full_path(filepath)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()

    def write_text(self, filepath: str, content: str) -> int:
        """Write text to a file. Returns bytes written."""
        full_path = self._get_full_path(filepath)
        self._ensure_directory(full_path)
        with open(full_path, "w", encoding="utf-8") as f:
            return f.write(content)

    def read_json(self, filepath: str) -> Any:
        """Read and parse a JSON file."""
        content = self.read_text(filepath)
        return json.loads(content)

    def write_json(self, filepath: str, data: Any, indent: int = 2) -> int:
        """Write data as JSON to a file."""
        content = json.dumps(data, indent=indent)
        return self.write_text(filepath, content)

    def read_lines(self, filepath: str) -> List[str]:
        """Read a file as a list of lines."""
        full_path = self._get_full_path(filepath)
        with open(full_path, "r", encoding="utf-8") as f:
            return f.readlines()

    def write_lines(self, filepath: str, lines: List[str]) -> int:
        """Write lines to a file."""
        full_path = self._get_full_path(filepath)
        self._ensure_directory(full_path)
        with open(full_path, "w", encoding="utf-8") as f:
            return f.writelines(lines)

    def append_text(self, filepath: str, content: str) -> int:
        """Append text to a file."""
        full_path = self._get_full_path(filepath)
        self._ensure_directory(full_path)
        with open(full_path, "a", encoding="utf-8") as f:
            return f.write(content)

    def read_binary(self, filepath: str) -> bytes:
        """Read a binary file."""
        full_path = self._get_full_path(filepath)
        with open(full_path, "rb") as f:
            return f.read()

    def write_binary(self, filepath: str, data: bytes) -> int:
        """Write binary data to a file."""
        full_path = self._get_full_path(filepath)
        self._ensure_directory(full_path)
        with open(full_path, "wb") as f:
            return f.write(data)

    def exists(self, filepath: str) -> bool:
        """Check if a file exists."""
        full_path = self._get_full_path(filepath)
        return os.path.exists(full_path)

    def delete(self, filepath: str) -> bool:
        """Delete a file."""
        full_path = self._get_full_path(filepath)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    def list_files(self, directory: str = "", pattern: Optional[str] = None) -> List[str]:
        """List files in a directory."""
        full_path = self._get_full_path(directory) if directory else self.base_path
        files = []
        for entry in os.listdir(full_path):
            entry_path = os.path.join(full_path, entry)
            if os.path.isfile(entry_path):
                if pattern is None or pattern in entry:
                    files.append(entry)
        return files

    def copy_file(self, src: str, dst: str) -> bool:
        """Copy a file."""
        content = self.read_binary(src)
        self.write_binary(dst, content)
        return True

    def _get_full_path(self, filepath: str) -> str:
        """Get the full path for a file."""
        if os.path.isabs(filepath):
            return filepath
        return os.path.join(self.base_path, filepath)

    def _ensure_directory(self, filepath: str) -> None:
        """Ensure the directory for a file exists."""
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
