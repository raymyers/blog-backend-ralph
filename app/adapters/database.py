"""Database adapter using SQLModel."""
from typing import Optional, List
from sqlmodel import Session, select

from app.domain.models import User, Article, Favorite
from app.ports.interfaces import UserRepository, ArticleRepository


class SQLModelUserRepository(UserRepository):
    """SQLModel implementation of UserRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def create(self, user: User) -> User:
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        return self.session.get(User, user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        statement = select(User).where(User.email == email)
        return self.session.exec(statement).first()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        statement = select(User).where(User.username == username)
        return self.session.exec(statement).first()
    
    async def update(self, user: User) -> User:
        db_user = self.session.get(User, user.id)
        if not db_user:
            return user

        db_user.email = user.email
        db_user.username = user.username
        db_user.password_hash = user.password_hash
        db_user.bio = user.bio
        db_user.image = user.image
        db_user.updated_at = user.updated_at

        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return db_user
class SQLModelArticleRepository(ArticleRepository):
    """SQLModel implementation of ArticleRepository."""
    
    def __init__(self, session: Session):
        self.session = session
    
    async def create(self, article: Article) -> Article:
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article
    
    async def get_by_slug(self, slug: str) -> Optional[Article]:
        statement = select(Article).where(Article.slug == slug)
        return self.session.exec(statement).first()
    
    async def get_by_id(self, article_id: int) -> Optional[Article]:
        return self.session.get(Article, article_id)
    
    async def get_all(self, limit: int = 20, offset: int = 0) -> List[Article]:
        statement = select(Article).order_by(Article.created_at.desc(), Article.id.desc()).offset(offset).limit(limit)
        return list(self.session.exec(statement).all())
    
    async def get_by_author(self, author_id: int, limit: int = 20, offset: int = 0) -> List[Article]:
        statement = select(Article).where(Article.author_id == author_id).order_by(Article.created_at.desc(), Article.id.desc()).offset(offset).limit(limit)
        return list(self.session.exec(statement).all())
    
    async def get_by_tag(self, tag: str, limit: int = 20, offset: int = 0) -> List[Article]:
        # Use JSON contains for SQLite
        from sqlalchemy import and_
        statement = select(Article).where(Article.tag_list_json.contains(f'"{tag}"')).order_by(Article.created_at.desc(), Article.id.desc()).offset(offset).limit(limit)
        return list(self.session.exec(statement).all())
    
    async def get_favorited_by(self, username: str, limit: int = 20, offset: int = 0) -> List[Article]:
        # Get user first
        user = self.session.exec(select(User).where(User.username == username)).first()
        if not user:
            return []
        
        # Get articles favorited by user
        statement = select(Article).join(Favorite).where(Favorite.user_id == user.id).order_by(Article.created_at.desc(), Article.id.desc()).offset(offset).limit(limit)
        return list(self.session.exec(statement).all())
    
    async def get_feed(self, follower_ids: List[int], limit: int = 20, offset: int = 0) -> List[Article]:
        if not follower_ids:
            return []
        statement = select(Article).where(Article.author_id.in_(follower_ids)).order_by(Article.created_at.desc(), Article.id.desc()).offset(offset).limit(limit)
        return list(self.session.exec(statement).all())
    

    async def count_all(self) -> int:
        from sqlalchemy import func
        statement = select(func.count()).select_from(Article)
        return self.session.exec(statement).one()

    async def count_by_author(self, author_id: int) -> int:
        from sqlalchemy import func
        statement = select(func.count()).select_from(Article).where(Article.author_id == author_id)
        return self.session.exec(statement).one()

    async def count_by_tag(self, tag: str) -> int:
        from sqlalchemy import func
        statement = select(func.count()).select_from(Article).where(Article.tag_list_json.contains(f'"{tag}"'))
        return self.session.exec(statement).one()

    async def count_favorited_by(self, username: str) -> int:
        from sqlalchemy import func
        user = self.session.exec(select(User).where(User.username == username)).first()
        if not user:
            return 0
        statement = select(func.count()).select_from(Article).join(Favorite).where(Favorite.user_id == user.id)
        return self.session.exec(statement).one()

    async def update(self, article: Article) -> Article:
        db_article = self.session.get(Article, article.id)
        if not db_article:
            return article
        
        db_article.title = article.title
        db_article.slug = article.slug
        db_article.description = article.description
        db_article.body = article.body
        db_article.tag_list = article.tag_list
        db_article.updated_at = article.updated_at
        db_article.favorites_count = article.favorites_count
        
        self.session.add(db_article)
        self.session.commit()
        self.session.refresh(db_article)
        return db_article
    
    async def delete(self, article_id: int) -> bool:
        article = self.session.get(Article, article_id)
        if not article:
            return False
        self.session.delete(article)
        self.session.commit()
        return True
    
    async def get_all_tags(self) -> List[str]:
        articles = self.session.exec(select(Article)).all()
        all_tags = set()
        for article in articles:
            all_tags.update(article.tag_list or [])
        return sorted(list(all_tags))
    
    async def is_favorited(self, article_id: int, user_id: int) -> bool:
        statement = select(Favorite).where(Favorite.article_id == article_id, Favorite.user_id == user_id)
        return self.session.exec(statement).first() is not None
    
    async def add_favorite(self, article_id: int, user_id: int) -> None:
        # Check if already favorited
        existing = await self.is_favorited(article_id, user_id)
        if existing:
            return
        
        favorite = Favorite(user_id=user_id, article_id=article_id)
        self.session.add(favorite)
        
        # Increment favorites count
        article = self.session.get(Article, article_id)
        if article:
            article.favorites_count += 1
        
        self.session.commit()
    
    async def remove_favorite(self, article_id: int, user_id: int) -> None:
        statement = select(Favorite).where(Favorite.article_id == article_id, Favorite.user_id == user_id)
        favorite = self.session.exec(statement).first()
        if favorite:
            self.session.delete(favorite)
            
            # Decrement favorites count
            article = self.session.get(Article, article_id)
            if article and article.favorites_count > 0:
                article.favorites_count -= 1
            
            self.session.commit()
