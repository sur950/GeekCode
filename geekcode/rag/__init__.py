"""
GeekCode RAG (Retrieval-Augmented Generation) module.

This module provides components for document chunking, embedding,
and retrieval for RAG-based workflows.

Requires optional deps: pip install geekcode[rag]
"""


def __getattr__(name):
    """Lazy imports to avoid requiring heavy dependencies at startup."""
    if name == "Chunker" or name == "ChunkingStrategy":
        from geekcode.rag.chunking import Chunker, ChunkingStrategy

        return Chunker if name == "Chunker" else ChunkingStrategy
    elif name == "Embedder":
        from geekcode.rag.embedding import Embedder

        return Embedder
    elif name == "Retriever":
        from geekcode.rag.retrieval import Retriever

        return Retriever
    raise AttributeError(f"module 'geekcode.rag' has no attribute {name}")


__all__ = ["Chunker", "ChunkingStrategy", "Embedder", "Retriever"]
