"""In-memory fakes for all repository and service ports."""

from app.domain.models import Article, Comment, User
from app.ports.interfaces import (
    ArticleRepository,
    CommentRepository,
    FollowRepository,
    PasswordHasher,
    TokenService,
    UserRepository,
)


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self._store: dict[int, User] = {}
        self._next_id = 1

    def create(self, user: User) -> User:
        saved = User(
            id=self._next_id,
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
            bio=user.bio,
            image=user.image,
        )
        self._store[self._next_id] = saved
        self._next_id += 1
        return saved

    def find_by_email(self, email: str) -> User | None:
        return next((u for u in self._store.values() if u.email == email), None)

    def find_by_username(self, username: str) -> User | None:
        return next((u for u in self._store.values() if u.username == username), None)

    def find_by_id(self, user_id: int) -> User | None:
        return self._store.get(user_id)

    def update(self, user: User) -> User:
        assert user.id is not None
        self._store[user.id] = user
        return user


class FakeArticleRepository(ArticleRepository):
    def __init__(self) -> None:
        self._store: dict[int, Article] = {}
        self._favorites: set[tuple[int, int]] = set()
        self._next_id = 1

    def create(self, article: Article) -> Article:
        saved = Article(
            id=self._next_id,
            slug=article.slug,
            title=article.title,
            description=article.description,
            body=article.body,
            author_id=article.author_id,
            tag_list=list(article.tag_list),
            favorites_count=0,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )
        self._store[self._next_id] = saved
        self._next_id += 1
        return saved

    def find_by_slug(self, slug: str) -> Article | None:
        return next((a for a in self._store.values() if a.slug == slug), None)

    def update(self, article: Article) -> Article:
        assert article.id is not None
        self._store[article.id] = article
        return article

    def delete(self, article: Article) -> None:
        assert article.id is not None
        self._store.pop(article.id, None)
        self._favorites = {(u, a) for u, a in self._favorites if a != article.id}

    def slug_exists(self, slug: str) -> bool:
        return any(a.slug == slug for a in self._store.values())

    def list_articles(self, tag, author_id, favorited_by_id, limit, offset):
        rows = list(self._store.values())
        if tag:
            rows = [a for a in rows if tag in a.tag_list]
        if author_id is not None:
            rows = [a for a in rows if a.author_id == author_id]
        if favorited_by_id is not None:
            favored = {a for u, a in self._favorites if u == favorited_by_id}
            rows = [a for a in rows if a.id in favored]
        rows.sort(key=lambda a: a.created_at, reverse=True)
        return rows[offset : offset + limit], len(rows)

    def list_feed(self, follower_id, limit, offset):
        from app.adapters.database import FollowRow  # noqa: F401 — not used in fake
        # feed is driven by follow repo; caller passes follower_id, we just delegate
        # For in-memory tests the follow repo is separate; we need followed_ids
        # The fake doesn't have access to the follow repo — the service will handle this
        # by calling _follows.is_following... but list_feed needs followed_ids.
        # In tests that exercise feed, use the SQL adapter or pass a stub.
        return [], 0

    def all_tags(self) -> list[str]:
        seen: set[str] = set()
        tags: list[str] = []
        for a in self._store.values():
            for t in a.tag_list:
                if t and t not in seen:
                    seen.add(t)
                    tags.append(t)
        return tags

    def add_favorite(self, user_id: int, article_id: int) -> None:
        if (user_id, article_id) in self._favorites:
            return
        self._favorites.add((user_id, article_id))
        if article_id in self._store:
            a = self._store[article_id]
            from dataclasses import replace
            self._store[article_id] = replace(a, favorites_count=a.favorites_count + 1)

    def remove_favorite(self, user_id: int, article_id: int) -> None:
        if (user_id, article_id) not in self._favorites:
            return
        self._favorites.discard((user_id, article_id))
        if article_id in self._store:
            a = self._store[article_id]
            from dataclasses import replace
            self._store[article_id] = replace(a, favorites_count=max(0, a.favorites_count - 1))

    def is_favorited(self, user_id: int, article_id: int) -> bool:
        return (user_id, article_id) in self._favorites


class FakeCommentRepository(CommentRepository):
    def __init__(self) -> None:
        self._store: dict[int, Comment] = {}
        self._next_id = 1

    def create(self, comment: Comment) -> Comment:
        saved = Comment(
            id=self._next_id,
            body=comment.body,
            article_id=comment.article_id,
            author_id=comment.author_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
        self._store[self._next_id] = saved
        self._next_id += 1
        return saved

    def list_for_article(self, article_id: int) -> list[Comment]:
        return [c for c in self._store.values() if c.article_id == article_id]

    def find_by_id(self, comment_id: int) -> Comment | None:
        return self._store.get(comment_id)

    def delete(self, comment: Comment) -> None:
        assert comment.id is not None
        self._store.pop(comment.id, None)


class FakeFollowRepository(FollowRepository):
    def __init__(self) -> None:
        self._follows: set[tuple[int, int]] = set()

    def follow(self, follower_id: int, followed_id: int) -> None:
        self._follows.add((follower_id, followed_id))

    def unfollow(self, follower_id: int, followed_id: int) -> None:
        self._follows.discard((follower_id, followed_id))

    def is_following(self, follower_id: int, followed_id: int) -> bool:
        return (follower_id, followed_id) in self._follows


class FakePasswordHasher(PasswordHasher):
    def hash(self, plain: str) -> str:
        return f"hashed:{plain}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


class FakeTokenService(TokenService):
    def __init__(self) -> None:
        self._counter = 0

    def create(self, user_id: int) -> str:
        self._counter += 1
        return f"token:{user_id}:{self._counter}"

    def decode(self, token: str) -> int | None:
        parts = token.split(":")
        return int(parts[1]) if len(parts) == 3 else None
