"""
GeekCode Chunking - Document chunking strategies for RAG.

This module provides various strategies for chunking documents
into smaller pieces suitable for embedding and retrieval.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import re


class ChunkingStrategy(Enum):
    """Available chunking strategies."""

    FIXED_SIZE = "fixed_size"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"
    CODE = "code"


@dataclass
class Chunk:
    """Represents a document chunk."""

    content: str
    index: int
    start_char: int
    end_char: int
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @property
    def length(self) -> int:
        """Return the length of the chunk content."""
        return len(self.content)


class BaseChunker(ABC):
    """Abstract base class for chunkers."""

    @abstractmethod
    def chunk(self, text: str) -> List[Chunk]:
        """Split text into chunks."""
        pass


class FixedSizeChunker(BaseChunker):
    """Chunk text into fixed-size pieces with optional overlap."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """
        Initialize the chunker.

        Args:
            chunk_size: Maximum size of each chunk in characters.
            overlap: Number of overlapping characters between chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> List[Chunk]:
        """Split text into fixed-size chunks."""
        chunks = []
        start = 0
        index = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))

            # Try to break at a sentence or word boundary
            if end < len(text):
                # Look for sentence boundary
                for sep in [". ", ".\n", "! ", "? ", "\n\n"]:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + len(sep)
                        break
                else:
                    # Fall back to word boundary
                    last_space = text.rfind(" ", start, end)
                    if last_space > start:
                        end = last_space + 1

            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        index=index,
                        start_char=start,
                        end_char=end,
                    )
                )
                index += 1

            start = end - self.overlap if end < len(text) else len(text)

        return chunks


class SentenceChunker(BaseChunker):
    """Chunk text by sentences, grouping into target-sized chunks."""

    def __init__(self, target_size: int = 1000, min_size: int = 100):
        """
        Initialize the chunker.

        Args:
            target_size: Target size for chunks in characters.
            min_size: Minimum chunk size in characters.
        """
        self.target_size = target_size
        self.min_size = min_size

    def chunk(self, text: str) -> List[Chunk]:
        """Split text into sentence-based chunks."""
        # Simple sentence splitting
        sentence_pattern = r"(?<=[.!?])\s+"
        sentences = re.split(sentence_pattern, text)

        chunks = []
        current_chunk = []
        current_length = 0
        current_start = 0
        index = 0
        char_pos = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.target_size and current_length >= self.min_size:
                # Save current chunk
                chunk_text = " ".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(
                        Chunk(
                            content=chunk_text,
                            index=index,
                            start_char=current_start,
                            end_char=char_pos,
                        )
                    )
                    index += 1

                current_chunk = [sentence]
                current_length = sentence_length
                current_start = char_pos
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

            char_pos += sentence_length + 1  # +1 for space

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk).strip()
            if chunk_text:
                chunks.append(
                    Chunk(
                        content=chunk_text,
                        index=index,
                        start_char=current_start,
                        end_char=len(text),
                    )
                )

        return chunks


class ParagraphChunker(BaseChunker):
    """Chunk text by paragraphs."""

    def __init__(self, max_size: int = 2000):
        """
        Initialize the chunker.

        Args:
            max_size: Maximum size of a chunk. Larger paragraphs will be split.
        """
        self.max_size = max_size
        self._fallback_chunker = FixedSizeChunker(chunk_size=max_size)

    def chunk(self, text: str) -> List[Chunk]:
        """Split text into paragraph-based chunks."""
        # Split on double newlines (paragraphs)
        paragraphs = re.split(r"\n\s*\n", text)

        chunks = []
        char_pos = 0
        index = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(para) > self.max_size:
                # Split large paragraphs
                sub_chunks = self._fallback_chunker.chunk(para)
                for sub in sub_chunks:
                    chunks.append(
                        Chunk(
                            content=sub.content,
                            index=index,
                            start_char=char_pos + sub.start_char,
                            end_char=char_pos + sub.end_char,
                        )
                    )
                    index += 1
            else:
                chunks.append(
                    Chunk(
                        content=para,
                        index=index,
                        start_char=char_pos,
                        end_char=char_pos + len(para),
                    )
                )
                index += 1

            char_pos += len(para) + 2  # +2 for \n\n

        return chunks


class CodeChunker(BaseChunker):
    """Chunk code by logical units (functions, classes, etc.)."""

    def __init__(self, max_size: int = 2000, language: Optional[str] = None):
        """
        Initialize the chunker.

        Args:
            max_size: Maximum size of a chunk.
            language: Programming language (for better splitting).
        """
        self.max_size = max_size
        self.language = language
        self._fallback_chunker = FixedSizeChunker(chunk_size=max_size)

    def chunk(self, text: str) -> List[Chunk]:
        """Split code into logical chunks."""
        # Patterns for common code structures
        patterns = [
            r"(?=\nclass\s+\w+)",  # Class definitions
            r"(?=\ndef\s+\w+)",  # Python function definitions
            r"(?=\nfunction\s+\w+)",  # JavaScript functions
            r"(?=\n(?:public|private|protected)\s+\w+)",  # Java/C# methods
        ]

        # Try to split by code structures
        combined_pattern = "|".join(patterns)
        parts = re.split(combined_pattern, text)

        chunks = []
        char_pos = 0
        index = 0

        for part in parts:
            part = part.strip()
            if not part:
                continue

            if len(part) > self.max_size:
                # Split large code blocks
                sub_chunks = self._fallback_chunker.chunk(part)
                for sub in sub_chunks:
                    chunks.append(
                        Chunk(
                            content=sub.content,
                            index=index,
                            start_char=char_pos + sub.start_char,
                            end_char=char_pos + sub.end_char,
                            metadata={"language": self.language},
                        )
                    )
                    index += 1
            else:
                chunks.append(
                    Chunk(
                        content=part,
                        index=index,
                        start_char=char_pos,
                        end_char=char_pos + len(part),
                        metadata={"language": self.language},
                    )
                )
                index += 1

            char_pos += len(part) + 1

        return chunks


class Chunker:
    """
    Main chunker class that delegates to strategy-specific chunkers.

    Example:
        >>> chunker = Chunker(strategy=ChunkingStrategy.SENTENCE)
        >>> chunks = chunker.chunk("Long document text...")
    """

    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.FIXED_SIZE,
        **kwargs,
    ):
        """
        Initialize the Chunker.

        Args:
            strategy: The chunking strategy to use.
            **kwargs: Strategy-specific parameters.
        """
        self.strategy = strategy
        self._chunker = self._create_chunker(strategy, **kwargs)

    def _create_chunker(self, strategy: ChunkingStrategy, **kwargs) -> BaseChunker:
        """Create the appropriate chunker for the strategy."""
        if strategy == ChunkingStrategy.FIXED_SIZE:
            return FixedSizeChunker(**kwargs)
        elif strategy == ChunkingStrategy.SENTENCE:
            return SentenceChunker(**kwargs)
        elif strategy == ChunkingStrategy.PARAGRAPH:
            return ParagraphChunker(**kwargs)
        elif strategy == ChunkingStrategy.CODE:
            return CodeChunker(**kwargs)
        else:
            return FixedSizeChunker(**kwargs)

    def chunk(self, text: str) -> List[Chunk]:
        """
        Split text into chunks.

        Args:
            text: The text to chunk.

        Returns:
            List of Chunk objects.
        """
        return self._chunker.chunk(text)
