from dataclasses import dataclass, field
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class User:
    email: str
    username: str
    hashed_password: str
    bio: str | None = None
    image: str | None = None
    id: int | None = None


@dataclass
class Article:
    slug: str
    title: str
    description: str
    body: str
    author_id: int
    tag_list: list[str] = field(default_factory=list)
    favorites_count: int = 0
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    id: int | None = None


@dataclass
class Comment:
    body: str
    article_id: int
    author_id: int
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    id: int | None = None


@dataclass
class Follow:
    follower_id: int
    followed_id: int


@dataclass
class Favorite:
    user_id: int
    article_id: int
