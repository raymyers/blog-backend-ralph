"""Ports (interfaces) for the application."""
from abc import ABC, abstractmethod
from typing import Optional, List

from app.domain.models import User, Article


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


class ArticleRepository(ABC):
    """Port for article data access."""
    
    @abstractmethod
    async def create(self, article: Article) -> Article:
        """Create a new article."""
        pass
    
    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Article]:
        """Get article by slug."""
        pass
    
    @abstractmethod
    async def get_by_id(self, article_id: int) -> Optional[Article]:
        """Get article by ID."""
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 20, offset: int = 0) -> List[Article]:
        """Get all articles with pagination."""
        pass
    
    @abstractmethod
    async def get_by_author(self, author_id: int, limit: int = 20, offset: int = 0) -> List[Article]:
        """Get articles by author."""
        pass
    
    @abstractmethod
    async def get_by_tag(self, tag: str, limit: int = 20, offset: int = 0) -> List[Article]:
        """Get articles by tag."""
        pass
    
    @abstractmethod
    async def get_favorited_by(self, username: str, limit: int = 20, offset: int = 0) -> List[Article]:
        """Get articles favorited by a user."""
        pass
    
    @abstractmethod
    async def get_feed(self, follower_ids: List[int], limit: int = 20, offset: int = 0) -> List[Article]:
        """Get articles from followed users."""
        pass
    
    @abstractmethod
    async def update(self, article: Article) -> Article:
        """Update article."""
        pass
    
    @abstractmethod
    async def delete(self, article_id: int) -> bool:
        """Delete article."""
        pass
    
    @abstractmethod
    async def get_all_tags(self) -> List[str]:
        """Get all unique tags."""
        pass
    
    @abstractmethod
    async def is_favorited(self, article_id: int, user_id: int) -> bool:
        """Check if article is favorited by user."""
        pass
    
    @abstractmethod
    async def add_favorite(self, article_id: int, user_id: int) -> None:
        """Add favorite."""
        pass
    
    @abstractmethod
    async def remove_favorite(self, article_id: int, user_id: int) -> None:
        """Remove favorite."""
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
