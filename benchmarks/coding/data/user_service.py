# User service module - needs unit tests
# This is sample input for Task 2: Add Unit Tests

from datetime import datetime
from typing import Optional, List, Dict, Any
import hashlib
import re


class UserService:
    """Service for managing user operations."""

    def __init__(self, database):
        self.db = database

    def create_user(self, email: str, name: str, password: str) -> Dict[str, Any]:
        """Create a new user."""
        if not self._validate_email(email):
            raise ValueError("Invalid email format")

        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        if self.db.find_by_email(email):
            raise ValueError("Email already exists")

        password_hash = self._hash_password(password)
        user = {
            "id": self.db.generate_id(),
            "email": email.lower(),
            "name": name.strip(),
            "password_hash": password_hash,
            "created_at": datetime.utcnow().isoformat(),
            "active": True,
        }
        self.db.insert("users", user)
        return self._sanitize_user(user)

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        user = self.db.find_by_id("users", user_id)
        if user:
            return self._sanitize_user(user)
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email."""
        user = self.db.find_by_email(email.lower())
        if user:
            return self._sanitize_user(user)
        return None

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update user fields."""
        user = self.db.find_by_id("users", user_id)
        if not user:
            raise ValueError("User not found")

        allowed_fields = {"name", "email"}
        for key in updates:
            if key not in allowed_fields:
                raise ValueError(f"Cannot update field: {key}")

        if "email" in updates:
            if not self._validate_email(updates["email"]):
                raise ValueError("Invalid email format")
            existing = self.db.find_by_email(updates["email"].lower())
            if existing and existing["id"] != user_id:
                raise ValueError("Email already in use")
            updates["email"] = updates["email"].lower()

        user.update(updates)
        user["updated_at"] = datetime.utcnow().isoformat()
        self.db.update("users", user_id, user)
        return self._sanitize_user(user)

    def delete_user(self, user_id: str) -> bool:
        """Soft delete a user."""
        user = self.db.find_by_id("users", user_id)
        if not user:
            return False

        user["active"] = False
        user["deleted_at"] = datetime.utcnow().isoformat()
        self.db.update("users", user_id, user)
        return True

    def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password."""
        user = self.db.find_by_email(email.lower())
        if not user:
            return None

        if not user.get("active", True):
            return None

        password_hash = self._hash_password(password)
        if user.get("password_hash") != password_hash:
            return None

        return self._sanitize_user(user)

    def list_users(self, page: int = 1, per_page: int = 20) -> List[Dict[str, Any]]:
        """List active users with pagination."""
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20

        offset = (page - 1) * per_page
        users = self.db.find_all("users", limit=per_page, offset=offset)
        return [self._sanitize_user(u) for u in users if u.get("active", True)]

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        user = self.db.find_by_id("users", user_id)
        if not user:
            raise ValueError("User not found")

        old_hash = self._hash_password(old_password)
        if user.get("password_hash") != old_hash:
            raise ValueError("Current password is incorrect")

        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters")

        user["password_hash"] = self._hash_password(new_password)
        user["updated_at"] = datetime.utcnow().isoformat()
        self.db.update("users", user_id, user)
        return True

    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def _hash_password(self, password: str) -> str:
        """Hash password with SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def _sanitize_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive fields from user dict."""
        return {k: v for k, v in user.items() if k != "password_hash"}
