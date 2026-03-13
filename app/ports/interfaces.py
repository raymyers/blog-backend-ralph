"""Ports (interfaces) for the application."""
from abc import ABC, abstractmethod
from typing import Optional, List

from app.domain.models import User


class UserRepository(ABC):
    """Port for user data access."""
    
    @abstractmethod
    async def create(self, user: User) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass
    
    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass
    
    @abstractmethod
    async def update(self, user: User) -> User:
        """Update user."""
        pass


class PasswordHasher(ABC):
    """Port for password hashing."""
    
    @abstractmethod
    def hash(self, password: str) -> str:
        """Hash a password."""
        pass
    
    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        pass


class TokenGenerator(ABC):
    """Port for JWT token generation."""
    
    @abstractmethod
    def create_access_token(self, data: dict) -> str:
        """Create a JWT access token."""
        pass
    
    @abstractmethod
    def decode_token(self, token: str) -> dict:
        """Decode and verify a JWT token."""
        pass
