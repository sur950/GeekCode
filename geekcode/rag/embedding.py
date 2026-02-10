"""
GeekCode Embedding - Text embedding for RAG.

This module provides embedding functionality using sentence-transformers
for generating vector representations of text chunks.
"""

from dataclasses import dataclass
from typing import List, Optional, Union
import numpy as np


@dataclass
class EmbeddingResult:
    """Result of embedding operation."""

    embeddings: np.ndarray
    model: str
    dimensions: int


class Embedder:
    """
    Text embedder using sentence-transformers.

    Generates vector embeddings for text chunks that can be used
    for semantic search and retrieval.

    Example:
        >>> embedder = Embedder()
        >>> embeddings = embedder.embed(["Hello world", "How are you?"])
    """

    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the Embedder.

        Args:
            model_name: Name of the sentence-transformers model to use.
                       Defaults to 'all-MiniLM-L6-v2'.
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model = None

    @property
    def model(self):
        """Lazy-load the embedding model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for embeddings. "
                    "Install with: pip install sentence-transformers"
                )
        return self._model

    def embed(self, texts: Union[str, List[str]]) -> EmbeddingResult:
        """
        Generate embeddings for text(s).

        Args:
            texts: A single text string or list of text strings.

        Returns:
            EmbeddingResult containing the embeddings.
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = self.model.encode(texts, convert_to_numpy=True)

        return EmbeddingResult(
            embeddings=embeddings,
            model=self.model_name,
            dimensions=embeddings.shape[1],
        )

    def embed_query(self, query: str) -> np.ndarray:
        """
        Embed a single query.

        Args:
            query: The query text to embed.

        Returns:
            Numpy array of the embedding.
        """
        result = self.embed(query)
        return result.embeddings[0]

    def embed_documents(self, documents: List[str]) -> np.ndarray:
        """
        Embed multiple documents.

        Args:
            documents: List of document texts to embed.

        Returns:
            Numpy array of embeddings (one per document).
        """
        result = self.embed(documents)
        return result.embeddings

    @property
    def dimensions(self) -> int:
        """Get the embedding dimensions for the current model."""
        # Embed a test string to get dimensions
        test_embedding = self.embed("test")
        return test_embedding.dimensions

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector.
            embedding2: Second embedding vector.

        Returns:
            Cosine similarity score (0 to 1).
        """
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def batch_similarity(
        self,
        query_embedding: np.ndarray,
        document_embeddings: np.ndarray,
    ) -> np.ndarray:
        """
        Calculate similarity between a query and multiple documents.

        Args:
            query_embedding: The query embedding vector.
            document_embeddings: Array of document embedding vectors.

        Returns:
            Array of similarity scores.
        """
        # Normalize embeddings
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = document_embeddings / np.linalg.norm(
            document_embeddings, axis=1, keepdims=True
        )

        # Calculate cosine similarities
        similarities = np.dot(doc_norms, query_norm)
        return similarities
