from typing import List, Optional

from sqlalchemy import func
from sqlmodel import Session, select

from app.domain.models import Article, Favorite, Follow, User
from app.ports.interfaces import ArticleRepository, UserRepository


class SQLModelUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        return self.session.exec(select(User).where(User.email == email)).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        return self.session.exec(select(User).where(User.username == username)).first()

    async def update(self, user: User) -> User:
        db_user = self.session.get(User, user.id)
        if not db_user:
            return user
        for field in ("email", "username", "password_hash", "bio", "image", "updated_at"):
            setattr(db_user, field, getattr(user, field))
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user


class SQLModelArticleRepository(ArticleRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    async def create(self, article: Article) -> Article:
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    async def get_by_slug(self, slug: str) -> Optional[Article]:
        return self.session.exec(select(Article).where(Article.slug == slug)).first()

    async def get_by_id(self, article_id: int) -> Optional[Article]:
        return self.session.get(Article, article_id)

    def _ordered(self, stmt):
        return stmt.order_by(Article.created_at.desc(), Article.id.desc())

    async def get_all(self, limit: int = 20, offset: int = 0) -> List[Article]:
        return list(self.session.exec(self._ordered(select(Article)).offset(offset).limit(limit)).all())

    async def get_by_author(self, author_id: int, limit: int = 20, offset: int = 0) -> List[Article]:
        stmt = self._ordered(select(Article).where(Article.author_id == author_id)).offset(offset).limit(limit)
        return list(self.session.exec(stmt).all())

    async def get_by_tag(self, tag: str, limit: int = 20, offset: int = 0) -> List[Article]:
        stmt = self._ordered(select(Article).where(Article.tag_list_json.contains(f'"{tag}"'))).offset(offset).limit(limit)
        return list(self.session.exec(stmt).all())

    async def get_favorited_by(self, username: str, limit: int = 20, offset: int = 0) -> List[Article]:
        user = self.session.exec(select(User).where(User.username == username)).first()
        if not user:
            return []
        stmt = self._ordered(select(Article).join(Favorite).where(Favorite.user_id == user.id)).offset(offset).limit(limit)
        return list(self.session.exec(stmt).all())

    async def get_feed(self, following_ids: List[int], limit: int = 20, offset: int = 0) -> List[Article]:
        if not following_ids:
            return []
        stmt = self._ordered(select(Article).where(Article.author_id.in_(following_ids))).offset(offset).limit(limit)
        return list(self.session.exec(stmt).all())

    async def count_all(self) -> int:
        return self.session.exec(select(func.count()).select_from(Article)).one()

    async def count_by_author(self, author_id: int) -> int:
        return self.session.exec(select(func.count()).select_from(Article).where(Article.author_id == author_id)).one()

    async def count_by_tag(self, tag: str) -> int:
        return self.session.exec(select(func.count()).select_from(Article).where(Article.tag_list_json.contains(f'"{tag}"'))).one()

    async def count_favorited_by(self, username: str) -> int:
        user = self.session.exec(select(User).where(User.username == username)).first()
        if not user:
            return 0
        return self.session.exec(select(func.count()).select_from(Article).join(Favorite).where(Favorite.user_id == user.id)).one()

    async def count_feed(self, following_ids: List[int]) -> int:
        if not following_ids:
            return 0
        return self.session.exec(select(func.count()).select_from(Article).where(Article.author_id.in_(following_ids))).one()

    async def update(self, article: Article) -> Article:
        db = self.session.get(Article, article.id)
        if not db:
            return article
        for field in ("title", "slug", "description", "body", "tag_list_json", "favorites_count", "updated_at"):
            setattr(db, field, getattr(article, field))
        self.session.add(db)
        self.session.commit()
        self.session.refresh(db)
        return db

    async def delete(self, article_id: int) -> bool:
        article = self.session.get(Article, article_id)
        if not article:
            return False
        self.session.delete(article)
        self.session.commit()
        return True

    async def get_all_tags(self) -> List[str]:
        articles = self.session.exec(select(Article)).all()
        tags: set[str] = set()
        for a in articles:
            tags.update(a.tag_list or [])
        return sorted(tags)

    async def is_favorited(self, article_id: int, user_id: int) -> bool:
        stmt = select(Favorite).where(Favorite.article_id == article_id, Favorite.user_id == user_id)
        return self.session.exec(stmt).first() is not None

    async def add_favorite(self, article_id: int, user_id: int) -> None:
        if await self.is_favorited(article_id, user_id):
            return
        self.session.add(Favorite(user_id=user_id, article_id=article_id))
        article = self.session.get(Article, article_id)
        if article:
            article.favorites_count += 1
        self.session.commit()

    async def remove_favorite(self, article_id: int, user_id: int) -> None:
        stmt = select(Favorite).where(Favorite.article_id == article_id, Favorite.user_id == user_id)
        fav = self.session.exec(stmt).first()
        if fav:
            self.session.delete(fav)
            article = self.session.get(Article, article_id)
            if article and article.favorites_count > 0:
                article.favorites_count -= 1
            self.session.commit()
