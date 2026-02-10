# Database abstraction layer - used by user_service.py
# This is sample input for Task 2: Add Unit Tests

import uuid
from typing import Optional, List, Dict, Any


class Database:
    """Simple in-memory database for testing."""

    def __init__(self):
        self._collections: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def generate_id(self) -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())

    def insert(self, collection: str, document: Dict[str, Any]) -> str:
        """Insert a document into a collection."""
        if collection not in self._collections:
            self._collections[collection] = {}

        doc_id = document.get("id", self.generate_id())
        self._collections[collection][doc_id] = document
        return doc_id

    def find_by_id(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Find a document by ID."""
        if collection not in self._collections:
            return None
        return self._collections[collection].get(doc_id)

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find a user by email (users collection only)."""
        if "users" not in self._collections:
            return None
        for doc in self._collections["users"].values():
            if doc.get("email") == email:
                return doc
        return None

    def find_all(
        self, collection: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Find all documents in a collection with pagination."""
        if collection not in self._collections:
            return []
        docs = list(self._collections[collection].values())
        return docs[offset : offset + limit]

    def update(self, collection: str, doc_id: str, document: Dict[str, Any]) -> bool:
        """Update a document."""
        if collection not in self._collections:
            return False
        if doc_id not in self._collections[collection]:
            return False
        self._collections[collection][doc_id] = document
        return True

    def delete(self, collection: str, doc_id: str) -> bool:
        """Delete a document."""
        if collection not in self._collections:
            return False
        if doc_id not in self._collections[collection]:
            return False
        del self._collections[collection][doc_id]
        return True

    def count(self, collection: str) -> int:
        """Count documents in a collection."""
        if collection not in self._collections:
            return 0
        return len(self._collections[collection])

    def clear(self, collection: Optional[str] = None) -> None:
        """Clear a collection or all collections."""
        if collection:
            if collection in self._collections:
                self._collections[collection] = {}
        else:
            self._collections = {}
