import re
from datetime import datetime
from typing import List, Optional

from app.domain.models import Article, User
from app.ports.interfaces import ArticleRepository
from app.schemas.article import ArticleCreate, ArticleUpdate


class ArticleService:
    def __init__(self, article_repository: ArticleRepository) -> None:
        self.article_repository = article_repository

    def _slugify(self, title: str) -> str:
        slug = re.sub(r"[^a-z0-9\s-]", "", title.lower())
        slug = re.sub(r"[\s]+", "-", slug)
        return re.sub(r"-+", "-", slug).strip("-")

    async def _unique_slug(self, base: str, exclude_id: Optional[int] = None) -> str:
        slug = base
        counter = 1
        while True:
            existing = await self.article_repository.get_by_slug(slug)
            if not existing or existing.id == exclude_id:
                return slug
            slug = f"{base}-{counter}"
            counter += 1

    async def create_article(self, author: User, data: ArticleCreate) -> Article:
        base_slug = self._slugify(data.title)
        slug = await self._unique_slug(base_slug)
        article = Article(
            slug=slug,
            title=data.title,
            description=data.description,
            body=data.body,
            author_id=author.id,
        )
        article.tag_list = data.tag_list or []
        return await self.article_repository.create(article)

    async def get_article_by_slug(self, slug: str, current_user_id: Optional[int] = None) -> Optional[dict]:
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return None
        favorited = False
        if current_user_id:
            favorited = await self.article_repository.is_favorited(article.id, current_user_id)
        return {"article": article, "favorited": favorited}

    async def update_article(self, slug: str, author: User, data: ArticleUpdate) -> Optional[Article]:
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return None
        if article.author_id != author.id:
            raise PermissionError("Not authorized")

        if data.title is not None:
            new_slug = self._slugify(data.title)
            if new_slug != article.slug:
                new_slug = await self._unique_slug(new_slug, exclude_id=article.id)
            article.slug = new_slug
            article.title = data.title

        if data.description is not None:
            article.description = data.description
        if data.body is not None:
            article.body = data.body
        if data.tag_list is not None:
            article.tag_list = data.tag_list

        article.updated_at = datetime.utcnow()
        return await self.article_repository.update(article)

    async def delete_article(self, slug: str, author: User) -> bool:
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return False
        if article.author_id != author.id:
            raise PermissionError("Not authorized")
        return await self.article_repository.delete(article.id)

    async def list_articles(
        self,
        tag: Optional[str] = None,
        author_id: Optional[int] = None,
        favorited: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Article]:
        if tag:
            return await self.article_repository.get_by_tag(tag, limit, offset)
        if author_id is not None:
            return await self.article_repository.get_by_author(author_id, limit, offset)
        if favorited:
            return await self.article_repository.get_favorited_by(favorited, limit, offset)
        return await self.article_repository.get_all(limit, offset)

    async def get_feed(self, following_ids: List[int], limit: int = 20, offset: int = 0) -> List[Article]:
        return await self.article_repository.get_feed(following_ids, limit, offset)

    async def get_all_tags(self) -> List[str]:
        return await self.article_repository.get_all_tags()

    async def favorite_article(self, slug: str, user_id: int) -> Optional[Article]:
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return None
        await self.article_repository.add_favorite(article.id, user_id)
        return await self.article_repository.get_by_slug(slug)

    async def unfavorite_article(self, slug: str, user_id: int) -> Optional[Article]:
        article = await self.article_repository.get_by_slug(slug)
        if not article:
            return None
        await self.article_repository.remove_favorite(article.id, user_id)
        return await self.article_repository.get_by_slug(slug)
