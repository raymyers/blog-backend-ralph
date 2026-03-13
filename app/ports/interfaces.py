from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.models import Article, User


class UserRepository(ABC):
    @abstractmethod
    async def create(self, user: User) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]: ...

    @abstractmethod
    async def update(self, user: User) -> User: ...


class ArticleRepository(ABC):
    @abstractmethod
    async def create(self, article: Article) -> Article: ...

    @abstractmethod
    async def get_by_slug(self, slug: str) -> Optional[Article]: ...

    @abstractmethod
    async def get_by_id(self, article_id: int) -> Optional[Article]: ...

    @abstractmethod
    async def get_all(self, limit: int = 20, offset: int = 0) -> List[Article]: ...

    @abstractmethod
    async def get_by_author(self, author_id: int, limit: int = 20, offset: int = 0) -> List[Article]: ...

    @abstractmethod
    async def get_by_tag(self, tag: str, limit: int = 20, offset: int = 0) -> List[Article]: ...

    @abstractmethod
    async def get_favorited_by(self, username: str, limit: int = 20, offset: int = 0) -> List[Article]: ...

    @abstractmethod
    async def get_feed(self, following_ids: List[int], limit: int = 20, offset: int = 0) -> List[Article]: ...

    @abstractmethod
    async def count_all(self) -> int: ...

    @abstractmethod
    async def count_by_author(self, author_id: int) -> int: ...

    @abstractmethod
    async def count_by_tag(self, tag: str) -> int: ...

    @abstractmethod
    async def count_favorited_by(self, username: str) -> int: ...

    @abstractmethod
    async def count_feed(self, following_ids: List[int]) -> int: ...

    @abstractmethod
    async def update(self, article: Article) -> Article: ...

    @abstractmethod
    async def delete(self, article_id: int) -> bool: ...

    @abstractmethod
    async def get_all_tags(self) -> List[str]: ...

    @abstractmethod
    async def is_favorited(self, article_id: int, user_id: int) -> bool: ...

    @abstractmethod
    async def add_favorite(self, article_id: int, user_id: int) -> None: ...

    @abstractmethod
    async def remove_favorite(self, article_id: int, user_id: int) -> None: ...


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str: ...

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...


class TokenGenerator(ABC):
    @abstractmethod
    def create_access_token(self, data: dict) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> dict: ...
