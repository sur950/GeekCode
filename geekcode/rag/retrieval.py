"""
GeekCode Retrieval - Vector search and retrieval for RAG.

This module provides retrieval functionality using ChromaDB
for storing and querying document embeddings.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from geekcode.rag.chunking import Chunk
from geekcode.rag.embedding import Embedder


@dataclass
class RetrievalResult:
    """Result from a retrieval query."""

    content: str
    score: float
    metadata: Dict[str, Any]
    chunk_id: str


class Retriever:
    """
    Vector-based retriever using ChromaDB.

    Stores document chunks as embeddings and retrieves the most
    relevant chunks for a given query.

    Example:
        >>> retriever = Retriever()
        >>> retriever.add_documents(chunks)
        >>> results = retriever.query("What is the main topic?", top_k=5)
    """

    def __init__(
        self,
        collection_name: str = "geekcode",
        persist_directory: Optional[str] = None,
        embedder: Optional[Embedder] = None,
    ):
        """
        Initialize the Retriever.

        Args:
            collection_name: Name of the ChromaDB collection.
            persist_directory: Directory to persist the database.
            embedder: Embedder instance to use. Creates new one if None.
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.embedder = embedder or Embedder()
        self._client = None
        self._collection = None

    @property
    def client(self):
        """Lazy-load the ChromaDB client."""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                if self.persist_directory:
                    Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
                    self._client = chromadb.PersistentClient(
                        path=self.persist_directory,
                        settings=Settings(anonymized_telemetry=False),
                    )
                else:
                    self._client = chromadb.Client(
                        Settings(anonymized_telemetry=False)
                    )
            except ImportError:
                raise ImportError(
                    "chromadb is required for retrieval. "
                    "Install with: pip install chromadb"
                )
        return self._client

    @property
    def collection(self):
        """Get or create the collection."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def add_documents(
        self,
        chunks: List[Chunk],
        source: Optional[str] = None,
    ) -> List[str]:
        """
        Add document chunks to the retriever.

        Args:
            chunks: List of Chunk objects to add.
            source: Optional source identifier (e.g., filename).

        Returns:
            List of chunk IDs that were added.
        """
        if not chunks:
            return []

        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedder.embed_documents(texts)

        # Prepare data for ChromaDB
        ids = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = str(uuid.uuid4())
            ids.append(chunk_id)

            metadata = {
                "index": chunk.index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
                **(chunk.metadata or {}),
            }
            if source:
                metadata["source"] = source

            metadatas.append(metadata)

        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            documents=texts,
            metadatas=metadatas,
        )

        return ids

    def query(
        self,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        Query the retriever for relevant chunks.

        Args:
            query: The query text.
            top_k: Number of results to return.
            filter: Optional metadata filter.

        Returns:
            List of RetrievalResult objects.
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k,
            where=filter,
            include=["documents", "metadatas", "distances"],
        )

        # Convert to RetrievalResult objects
        retrieval_results = []

        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                # ChromaDB returns distances, convert to similarity scores
                # For cosine distance: similarity = 1 - distance
                distance = results["distances"][0][i] if results["distances"] else 0
                score = 1 - distance

                retrieval_results.append(
                    RetrievalResult(
                        content=results["documents"][0][i],
                        score=score,
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        chunk_id=chunk_id,
                    )
                )

        return retrieval_results

    def delete(self, chunk_ids: List[str]) -> None:
        """
        Delete chunks by their IDs.

        Args:
            chunk_ids: List of chunk IDs to delete.
        """
        if chunk_ids:
            self.collection.delete(ids=chunk_ids)

    def delete_by_source(self, source: str) -> None:
        """
        Delete all chunks from a specific source.

        Args:
            source: The source identifier to delete.
        """
        # Get all chunks with this source
        results = self.collection.get(
            where={"source": source},
            include=[],
        )

        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def clear(self) -> None:
        """Clear all documents from the collection."""
        # Delete and recreate the collection
        self.client.delete_collection(self.collection_name)
        self._collection = None

    def count(self) -> int:
        """Get the number of documents in the collection."""
        return self.collection.count()

    def get_all_sources(self) -> List[str]:
        """Get all unique source identifiers."""
        results = self.collection.get(include=["metadatas"])
        sources = set()

        for metadata in results.get("metadatas", []):
            if metadata and "source" in metadata:
                sources.add(metadata["source"])

        return sorted(sources)
