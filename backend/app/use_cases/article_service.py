import re
import uuid
from dataclasses import replace

from app.domain.models import Article
from app.ports.interfaces import ArticleRepository, FollowRepository, UserRepository
from app.use_cases.errors import ForbiddenError, NotFoundError, ValidationError

_UNSET = object()  # sentinel for distinguishing "not provided" from None/[]


def _slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug


class ArticleService:
    def __init__(
        self,
        articles: ArticleRepository,
        users: UserRepository,
        follows: FollowRepository,
    ) -> None:
        self._articles = articles
        self._users = users
        self._follows = follows

    def _unique_slug(self, title: str) -> str:
        base = _slugify(title)
        slug = base
        while self._articles.slug_exists(slug):
            slug = f"{base}-{uuid.uuid4().hex[:6]}"
        return slug

    def create(
        self,
        author_id: int,
        title: str,
        description: str,
        body: str,
        tag_list: list[str] | None = None,
    ) -> Article:
        if not title.strip():
            raise ValidationError("title", "can't be blank")
        if not description.strip():
            raise ValidationError("description", "can't be blank")
        if not body.strip():
            raise ValidationError("body", "can't be blank")

        slug = self._unique_slug(title)
        return self._articles.create(
            Article(
                slug=slug,
                title=title,
                description=description,
                body=body,
                author_id=author_id,
                tag_list=tag_list or [],
            )
        )

    def get(self, slug: str) -> Article:
        article = self._articles.find_by_slug(slug)
        if article is None:
            raise NotFoundError(slug)
        return article

    def update(
        self,
        slug: str,
        requester_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        body: str | None = None,
        tag_list: object = _UNSET,
    ) -> Article:
        article = self._articles.find_by_slug(slug)
        if article is None:
            raise NotFoundError(slug)
        if article.author_id != requester_id:
            raise ForbiddenError()

        new_slug = self._unique_slug(title) if title is not None else article.slug
        new_tags = article.tag_list if tag_list is _UNSET else list(tag_list)  # type: ignore[arg-type]
        updated = replace(
            article,
            slug=new_slug,
            title=title if title is not None else article.title,
            description=description if description is not None else article.description,
            body=body if body is not None else article.body,
            tag_list=new_tags,
        )
        return self._articles.update(updated)

    def delete(self, slug: str, requester_id: int) -> None:
        article = self._articles.find_by_slug(slug)
        if article is None:
            raise NotFoundError(slug)
        if article.author_id != requester_id:
            raise ForbiddenError()
        self._articles.delete(article)

    def list_articles(
        self,
        tag: str | None = None,
        author: str | None = None,
        favorited: str | None = None,
        limit: int = 20,
        offset: int = 0,
        viewer_id: int | None = None,
    ) -> tuple[list[Article], int]:
        author_id = None
        if author:
            u = self._users.find_by_username(author)
            author_id = u.id if u else -1

        favorited_by_id = None
        if favorited:
            u = self._users.find_by_username(favorited)
            favorited_by_id = u.id if u else -1

        return self._articles.list_articles(tag, author_id, favorited_by_id, limit, offset)

    def list_feed(
        self,
        requester_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[Article], int]:
        return self._articles.list_feed(requester_id, limit, offset)

    def all_tags(self) -> list[str]:
        return self._articles.all_tags()

    def favorite(self, slug: str, user_id: int) -> Article:
        article = self._articles.find_by_slug(slug)
        if article is None:
            raise NotFoundError(slug)
        assert article.id is not None
        self._articles.add_favorite(user_id, article.id)
        return self._articles.find_by_slug(slug)  # type: ignore[return-value]

    def unfavorite(self, slug: str, user_id: int) -> Article:
        article = self._articles.find_by_slug(slug)
        if article is None:
            raise NotFoundError(slug)
        assert article.id is not None
        self._articles.remove_favorite(user_id, article.id)
        return self._articles.find_by_slug(slug)  # type: ignore[return-value]

    def is_favorited(self, article: Article, user_id: int | None) -> bool:
        if user_id is None or article.id is None:
            return False
        return self._articles.is_favorited(user_id, article.id)

    def is_following_author(self, article: Article, viewer_id: int | None) -> bool:
        if viewer_id is None:
            return False
        return self._follows.is_following(viewer_id, article.author_id)
