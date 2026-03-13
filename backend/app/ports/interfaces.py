from abc import ABC, abstractmethod

from app.domain.models import Article, Comment, Follow, User


class UserRepository(ABC):
    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def find_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def find_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    def find_by_id(self, user_id: int) -> User | None: ...

    @abstractmethod
    def update(self, user: User) -> User: ...


class ArticleRepository(ABC):
    @abstractmethod
    def create(self, article: Article) -> Article: ...

    @abstractmethod
    def find_by_slug(self, slug: str) -> Article | None: ...

    @abstractmethod
    def update(self, article: Article) -> Article: ...

    @abstractmethod
    def delete(self, article: Article) -> None: ...

    @abstractmethod
    def list_articles(
        self,
        tag: str | None,
        author_id: int | None,
        favorited_by_id: int | None,
        limit: int,
        offset: int,
    ) -> tuple[list[Article], int]: ...

    @abstractmethod
    def list_feed(
        self,
        follower_id: int,
        limit: int,
        offset: int,
    ) -> tuple[list[Article], int]: ...

    @abstractmethod
    def all_tags(self) -> list[str]: ...

    @abstractmethod
    def slug_exists(self, slug: str) -> bool: ...

    @abstractmethod
    def add_favorite(self, user_id: int, article_id: int) -> None: ...

    @abstractmethod
    def remove_favorite(self, user_id: int, article_id: int) -> None: ...

    @abstractmethod
    def is_favorited(self, user_id: int, article_id: int) -> bool: ...


class CommentRepository(ABC):
    @abstractmethod
    def create(self, comment: Comment) -> Comment: ...

    @abstractmethod
    def list_for_article(self, article_id: int) -> list[Comment]: ...

    @abstractmethod
    def find_by_id(self, comment_id: int) -> Comment | None: ...

    @abstractmethod
    def delete(self, comment: Comment) -> None: ...


class FollowRepository(ABC):
    @abstractmethod
    def follow(self, follower_id: int, followed_id: int) -> None: ...

    @abstractmethod
    def unfollow(self, follower_id: int, followed_id: int) -> None: ...

    @abstractmethod
    def is_following(self, follower_id: int, followed_id: int) -> bool: ...


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, plain: str) -> str: ...

    @abstractmethod
    def verify(self, plain: str, hashed: str) -> bool: ...


class TokenService(ABC):
    @abstractmethod
    def create(self, user_id: int) -> str: ...

    @abstractmethod
    def decode(self, token: str) -> int | None: ...
