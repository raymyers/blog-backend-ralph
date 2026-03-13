from datetime import datetime, timezone

from sqlmodel import Field, Session, SQLModel, col, create_engine, select

from app.domain.models import (
    Article as DomainArticle,
)
from app.domain.models import (
    Comment as DomainComment,
)
from app.domain.models import (
    User as DomainUser,
)
from app.ports.interfaces import (
    ArticleRepository,
    CommentRepository,
    FollowRepository,
    UserRepository,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# SQLModel table definitions
# ---------------------------------------------------------------------------


class UserRow(SQLModel, table=True):
    __tablename__ = "user"
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    bio: str | None = None
    image: str | None = None


class ArticleRow(SQLModel, table=True):
    __tablename__ = "article"
    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    title: str
    description: str
    body: str
    author_id: int = Field(foreign_key="user.id")
    tag_list: str = Field(default="")  # pipe-separated
    favorites_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class CommentRow(SQLModel, table=True):
    __tablename__ = "comment"
    id: int | None = Field(default=None, primary_key=True)
    body: str
    article_id: int = Field(foreign_key="article.id")
    author_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class FollowRow(SQLModel, table=True):
    __tablename__ = "follow"
    follower_id: int = Field(foreign_key="user.id", primary_key=True)
    followed_id: int = Field(foreign_key="user.id", primary_key=True)


class FavoriteRow(SQLModel, table=True):
    __tablename__ = "favorite"
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    article_id: int = Field(foreign_key="article.id", primary_key=True)


# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------


def _user_to_domain(row: UserRow) -> DomainUser:
    return DomainUser(
        id=row.id,
        email=row.email,
        username=row.username,
        hashed_password=row.hashed_password,
        bio=row.bio,
        image=row.image,
    )


def _article_to_domain(row: ArticleRow) -> DomainArticle:
    return DomainArticle(
        id=row.id,
        slug=row.slug,
        title=row.title,
        description=row.description,
        body=row.body,
        author_id=row.author_id,
        tag_list=[t for t in row.tag_list.split("|") if t],
        favorites_count=row.favorites_count,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _comment_to_domain(row: CommentRow) -> DomainComment:
    return DomainComment(
        id=row.id,
        body=row.body,
        article_id=row.article_id,
        author_id=row.author_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


# ---------------------------------------------------------------------------
# Repositories
# ---------------------------------------------------------------------------


class SQLUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, user: DomainUser) -> DomainUser:
        row = UserRow(
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
            bio=user.bio,
            image=user.image,
        )
        self._s.add(row)
        self._s.commit()
        self._s.refresh(row)
        return _user_to_domain(row)

    def find_by_email(self, email: str) -> DomainUser | None:
        row = self._s.exec(select(UserRow).where(UserRow.email == email)).first()
        return _user_to_domain(row) if row else None

    def find_by_username(self, username: str) -> DomainUser | None:
        row = self._s.exec(select(UserRow).where(UserRow.username == username)).first()
        return _user_to_domain(row) if row else None

    def find_by_id(self, user_id: int) -> DomainUser | None:
        row = self._s.get(UserRow, user_id)
        return _user_to_domain(row) if row else None

    def update(self, user: DomainUser) -> DomainUser:
        row = self._s.get(UserRow, user.id)
        if row is None:
            raise ValueError(f"User {user.id} not found")
        row.email = user.email
        row.username = user.username
        row.hashed_password = user.hashed_password
        row.bio = user.bio
        row.image = user.image
        self._s.add(row)
        self._s.commit()
        self._s.refresh(row)
        return _user_to_domain(row)


class SQLArticleRepository(ArticleRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, article: DomainArticle) -> DomainArticle:
        row = ArticleRow(
            slug=article.slug,
            title=article.title,
            description=article.description,
            body=article.body,
            author_id=article.author_id,
            tag_list="|".join(article.tag_list),
            favorites_count=0,
            created_at=article.created_at,
            updated_at=article.updated_at,
        )
        self._s.add(row)
        self._s.commit()
        self._s.refresh(row)
        return _article_to_domain(row)

    def find_by_slug(self, slug: str) -> DomainArticle | None:
        row = self._s.exec(select(ArticleRow).where(ArticleRow.slug == slug)).first()
        return _article_to_domain(row) if row else None

    def update(self, article: DomainArticle) -> DomainArticle:
        row = self._s.get(ArticleRow, article.id)
        if row is None:
            raise ValueError(f"Article {article.id} not found")
        row.slug = article.slug
        row.title = article.title
        row.description = article.description
        row.body = article.body
        row.tag_list = "|".join(article.tag_list)
        row.updated_at = _now()
        self._s.add(row)
        self._s.commit()
        self._s.refresh(row)
        return _article_to_domain(row)

    def delete(self, article: DomainArticle) -> None:
        row = self._s.get(ArticleRow, article.id)
        if row:
            # cascade delete favorites and comments
            for fav in self._s.exec(select(FavoriteRow).where(FavoriteRow.article_id == article.id)).all():
                self._s.delete(fav)
            for cmt in self._s.exec(select(CommentRow).where(CommentRow.article_id == article.id)).all():
                self._s.delete(cmt)
            self._s.delete(row)
            self._s.commit()

    def slug_exists(self, slug: str) -> bool:
        return self._s.exec(select(ArticleRow).where(ArticleRow.slug == slug)).first() is not None

    def list_articles(
        self,
        tag: str | None,
        author_id: int | None,
        favorited_by_id: int | None,
        limit: int,
        offset: int,
    ) -> tuple[list[DomainArticle], int]:
        stmt = select(ArticleRow)
        if tag:
            stmt = stmt.where(col(ArticleRow.tag_list).contains(tag))
        if author_id is not None:
            stmt = stmt.where(ArticleRow.author_id == author_id)
        if favorited_by_id is not None:
            favored_ids = [
                r.article_id
                for r in self._s.exec(
                    select(FavoriteRow).where(FavoriteRow.user_id == favorited_by_id)
                ).all()
            ]
            stmt = stmt.where(col(ArticleRow.id).in_(favored_ids))
        stmt = stmt.order_by(col(ArticleRow.created_at).desc())
        all_rows = self._s.exec(stmt).all()
        total = len(all_rows)
        page = all_rows[offset : offset + limit]
        return [_article_to_domain(r) for r in page], total

    def list_feed(
        self,
        follower_id: int,
        limit: int,
        offset: int,
    ) -> tuple[list[DomainArticle], int]:
        followed_ids = [
            r.followed_id
            for r in self._s.exec(
                select(FollowRow).where(FollowRow.follower_id == follower_id)
            ).all()
        ]
        stmt = (
            select(ArticleRow)
            .where(col(ArticleRow.author_id).in_(followed_ids))
            .order_by(col(ArticleRow.created_at).desc())
        )
        all_rows = self._s.exec(stmt).all()
        total = len(all_rows)
        page = all_rows[offset : offset + limit]
        return [_article_to_domain(r) for r in page], total

    def all_tags(self) -> list[str]:
        rows = self._s.exec(select(ArticleRow)).all()
        seen: set[str] = set()
        tags: list[str] = []
        for row in rows:
            for tag in row.tag_list.split("|"):
                if tag and tag not in seen:
                    seen.add(tag)
                    tags.append(tag)
        return tags

    def add_favorite(self, user_id: int, article_id: int) -> None:
        existing = self._s.exec(
            select(FavoriteRow)
            .where(FavoriteRow.user_id == user_id)
            .where(FavoriteRow.article_id == article_id)
        ).first()
        if existing:
            return
        self._s.add(FavoriteRow(user_id=user_id, article_id=article_id))
        row = self._s.get(ArticleRow, article_id)
        if row:
            row.favorites_count += 1
            self._s.add(row)
        self._s.commit()

    def remove_favorite(self, user_id: int, article_id: int) -> None:
        existing = self._s.exec(
            select(FavoriteRow)
            .where(FavoriteRow.user_id == user_id)
            .where(FavoriteRow.article_id == article_id)
        ).first()
        if not existing:
            return
        self._s.delete(existing)
        row = self._s.get(ArticleRow, article_id)
        if row and row.favorites_count > 0:
            row.favorites_count -= 1
            self._s.add(row)
        self._s.commit()

    def is_favorited(self, user_id: int, article_id: int) -> bool:
        return (
            self._s.exec(
                select(FavoriteRow)
                .where(FavoriteRow.user_id == user_id)
                .where(FavoriteRow.article_id == article_id)
            ).first()
            is not None
        )


class SQLCommentRepository(CommentRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def create(self, comment: DomainComment) -> DomainComment:
        row = CommentRow(
            body=comment.body,
            article_id=comment.article_id,
            author_id=comment.author_id,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
        )
        self._s.add(row)
        self._s.commit()
        self._s.refresh(row)
        return _comment_to_domain(row)

    def list_for_article(self, article_id: int) -> list[DomainComment]:
        rows = self._s.exec(select(CommentRow).where(CommentRow.article_id == article_id)).all()
        return [_comment_to_domain(r) for r in rows]

    def find_by_id(self, comment_id: int) -> DomainComment | None:
        row = self._s.get(CommentRow, comment_id)
        return _comment_to_domain(row) if row else None

    def delete(self, comment: DomainComment) -> None:
        row = self._s.get(CommentRow, comment.id)
        if row:
            self._s.delete(row)
            self._s.commit()


class SQLFollowRepository(FollowRepository):
    def __init__(self, session: Session) -> None:
        self._s = session

    def follow(self, follower_id: int, followed_id: int) -> None:
        existing = self._s.exec(
            select(FollowRow)
            .where(FollowRow.follower_id == follower_id)
            .where(FollowRow.followed_id == followed_id)
        ).first()
        if existing:
            return
        self._s.add(FollowRow(follower_id=follower_id, followed_id=followed_id))
        self._s.commit()

    def unfollow(self, follower_id: int, followed_id: int) -> None:
        existing = self._s.exec(
            select(FollowRow)
            .where(FollowRow.follower_id == follower_id)
            .where(FollowRow.followed_id == followed_id)
        ).first()
        if existing:
            self._s.delete(existing)
            self._s.commit()

    def is_following(self, follower_id: int, followed_id: int) -> bool:
        return (
            self._s.exec(
                select(FollowRow)
                .where(FollowRow.follower_id == follower_id)
                .where(FollowRow.followed_id == followed_id)
            ).first()
            is not None
        )
