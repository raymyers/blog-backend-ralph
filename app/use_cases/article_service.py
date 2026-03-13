"""Article service for business logic."""
import re
from datetime import datetime
from typing import Optional, List

from app.domain.models import Article, User
from app.schemas.article import ArticleCreate, ArticleUpdate
from app.ports.interfaces import ArticleRepository


class ArticleService:
    """Service for article operations."""
    
    def __init__(self, article_repository: ArticleRepository):
        self.article_repository = article_repository
    
    def _generate_slug(self, title: str) -> str:
        """Generate a slug from title."""
        # Convert to lowercase, replace spaces with hyphens, remove non-alphanumeric
        slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')
    
    async def create_article(self, author: User, article_data: ArticleCreate) -> Article:
        """Create a new article."""
        slug = self._generate_slug(article_data.title)
        
        # Check for slug collision and append suffix if needed
        base_slug = slug
        counter = 1
        while await self.article_repository.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Use the property setter to properly set tag_list_json
        article = Article(
            slug=slug,
            title=article_data.title,
            description=article_data.description,
            body=article_data.body,
            author_id=author.id,
        )
        article.tag_list = article_data.tag_list or []
        
        return await self.article_repository.create(article)
    
    async def get_article_by_slug(self, slug: str, current_user_id: Optional[int] = None) -> Optional[dict]:
        """Get article by slug with author info."""
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return None
        
        favorited = False
        if current_user_id:
            favorited = await self.article_repository.is_favorited(article.id, current_user_id)
        
        return {
            "article": article,
            "favorited": favorited,
        }
    
    async def update_article(self, slug: str, author: User, article_data: ArticleUpdate) -> Optional[Article]:
        """Update an article."""
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return None
        
        # Check ownership
        if article.author_id != author.id:
            raise PermissionError("Not authorized to edit this article")
        
        # Update fields if provided
        if article_data.title is not None:
            new_slug = self._generate_slug(article_data.title)
            # Only update slug if it actually changed
            if new_slug != article.slug:
                # Check for collision
                existing = await self.article_repository.get_by_slug(new_slug)
                if existing and existing.id != article.id:
                    # Append suffix
                    base_slug = new_slug
                    counter = 1
                    while await self.article_repository.get_by_slug(new_slug):
                        new_slug = f"{base_slug}-{counter}"
                        counter += 1
                article.slug = new_slug
            article.title = article_data.title
        
        if article_data.description is not None:
            article.description = article_data.description
        
        if article_data.body is not None:
            article.body = article_data.body
        
        if article_data.tag_list is not None:
            article.tag_list = article_data.tag_list
        
        article.updated_at = datetime.utcnow()
        
        return await self.article_repository.update(article)
    
    async def delete_article(self, slug: str, author: User) -> bool:
        """Delete an article."""
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return False
        
        # Check ownership
        if article.author_id != author.id:
            raise PermissionError("Not authorized to delete this article")
        
        return await self.article_repository.delete(article.id)
    
    async def list_articles(
        self,
        tag: Optional[str] = None,
        author: Optional[str] = None,
        favorited: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        current_user_id: Optional[int] = None,
    ) -> tuple[List[Article], int]:
        """List articles with filters."""
        articles: List[Article]
        
        if tag:
            articles = await self.article_repository.get_by_tag(tag, limit, offset)
        elif author:
            # Get author user first
            from app.adapters.database import SQLModelUserRepository
            from app.database import Session
            with Session() as session:
                user_repo = SQLModelUserRepository(session)
                author_user = await user_repo.get_by_username(author)
                if author_user:
                    articles = await self.article_repository.get_by_author(author_user.id, limit, offset)
                else:
                    articles = []
        elif favorited:
            articles = await self.article_repository.get_favorited_by(favorited, limit, offset)
        else:
            articles = await self.article_repository.get_all(limit, offset)
        
        # Get total count (simplified - would need proper count queries for production)
        total = len(articles)
        
        return articles, total
    
    async def get_feed(self, follower_ids: List[int], limit: int = 20, offset: int = 0) -> List[Article]:
        """Get feed of articles from followed users."""
        return await self.article_repository.get_feed(follower_ids, limit, offset)
    
    async def get_all_tags(self) -> List[str]:
        """Get all tags."""
        return await self.article_repository.get_all_tags()
    
    async def favorite_article(self, slug: str, user_id: int) -> Optional[Article]:
        """Favorite an article."""
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return None
        
        await self.article_repository.add_favorite(article.id, user_id)
        
        # Refresh to get updated count
        return await self.article_repository.get_by_slug(slug)
    
    async def unfavorite_article(self, slug: str, user_id: int) -> Optional[Article]:
        """Unfavorite an article."""
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return None
        
        await self.article_repository.remove_favorite(article.id, user_id)
        
        # Refresh to get updated count
        return await self.article_repository.get_by_slug(slug)
