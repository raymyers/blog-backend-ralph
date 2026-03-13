from typing import Any

from fastapi import APIRouter, HTTPException

from app.deps import (
    ArticleServiceDep,
    OptionalUserIdDep,
    ProfileServiceDep,
    RequiredUserIdDep,
    UserServiceDep,
)
from app.domain.models import Article, User
from app.use_cases.article_service import ArticleService
from app.use_cases.errors import ForbiddenError, NotFoundError, ValidationError

router = APIRouter()


def _author_dict(user: User, following: bool) -> dict[str, Any]:
    return {
        "username": user.username,
        "bio": user.bio,
        "image": user.image,
        "following": following,
    }


def _article_dict(
    article: Article,
    author: User,
    favorited: bool,
    following: bool,
    include_body: bool = True,
) -> dict[str, Any]:
    d: dict[str, Any] = {
        "slug": article.slug,
        "title": article.title,
        "description": article.description,
        "tagList": article.tag_list,
        "createdAt": article.created_at.isoformat().replace("+00:00", "Z"),
        "updatedAt": article.updated_at.isoformat().replace("+00:00", "Z"),
        "favorited": favorited,
        "favoritesCount": article.favorites_count,
        "author": _author_dict(author, following),
    }
    if include_body:
        d["body"] = article.body
    return d


def _resolve_article(
    article: Article,
    article_svc: ArticleService,
    profile_svc,
    viewer_id: int | None,
    include_body: bool = True,
) -> dict[str, Any]:
    from app.use_cases.errors import NotFoundError as NFE

    try:
        author, following = profile_svc.get_profile(
            _get_username_for_id(profile_svc, article.author_id),
            viewer_id=viewer_id,
        )
    except NFE:
        raise HTTPException(404, detail={"errors": {"body": ["Author not found"]}})

    favorited = article_svc.is_favorited(article, viewer_id)
    return _article_dict(article, author, favorited, following, include_body=include_body)


def _get_username_for_id(profile_svc, user_id: int) -> str:
    """Look up username by user_id via the profile service's user repository."""
    user = profile_svc._users.find_by_id(user_id)
    if user is None:
        raise NotFoundError(str(user_id))
    return user.username


# GET /api/articles/feed must be registered BEFORE /api/articles/{slug}
@router.get("/articles/feed")
def feed_articles(
    user_id: RequiredUserIdDep,
    article_svc: ArticleServiceDep,
    profile_svc: ProfileServiceDep,
    limit: int = 20,
    offset: int = 0,
):
    articles, total = article_svc.list_feed(user_id, limit=limit, offset=offset)
    items = [
        _resolve_article(a, article_svc, profile_svc, user_id, include_body=False)
        for a in articles
    ]
    return {"articles": items, "articlesCount": total}


@router.get("/articles")
def list_articles(
    viewer_id: OptionalUserIdDep,
    article_svc: ArticleServiceDep,
    profile_svc: ProfileServiceDep,
    tag: str | None = None,
    author: str | None = None,
    favorited: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    articles, total = article_svc.list_articles(
        tag=tag,
        author=author,
        favorited=favorited,
        limit=limit,
        offset=offset,
    )
    items = [
        _resolve_article(a, article_svc, profile_svc, viewer_id, include_body=False)
        for a in articles
    ]
    return {"articles": items, "articlesCount": total}


@router.post("/articles", status_code=201)
def create_article(
    body: dict[str, Any],
    user_id: RequiredUserIdDep,
    article_svc: ArticleServiceDep,
    profile_svc: ProfileServiceDep,
):
    data = body.get("article", {})
    try:
        article = article_svc.create(
            author_id=user_id,
            title=data.get("title", ""),
            description=data.get("description", ""),
            body=data.get("body", ""),
            tag_list=data.get("tagList", []),
        )
    except ValidationError as e:
        raise HTTPException(422, detail={"errors": {e.field: [e.message]}})
    return {"article": _resolve_article(article, article_svc, profile_svc, user_id)}


@router.get("/articles/{slug}")
def get_article(
    slug: str,
    viewer_id: OptionalUserIdDep,
    article_svc: ArticleServiceDep,
    profile_svc: ProfileServiceDep,
):
    try:
        article = article_svc.get(slug)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"body": ["Not Found"]}})
    return {"article": _resolve_article(article, article_svc, profile_svc, viewer_id)}


@router.put("/articles/{slug}")
def update_article(
    slug: str,
    body: dict[str, Any],
    user_id: RequiredUserIdDep,
    article_svc: ArticleServiceDep,
    profile_svc: ProfileServiceDep,
):
    data = body.get("article", {})
    kwargs: dict[str, Any] = {}
    if "title" in data:
        kwargs["title"] = data["title"]
    if "description" in data:
        kwargs["description"] = data["description"]
    if "body" in data:
        kwargs["body"] = data["body"]

    try:
        article = article_svc.update(slug, user_id, **kwargs)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"body": ["Not Found"]}})
    except ForbiddenError:
        raise HTTPException(403, detail={"errors": {"body": ["Forbidden"]}})
    return {"article": _resolve_article(article, article_svc, profile_svc, user_id)}


@router.delete("/articles/{slug}", status_code=200)
def delete_article(
    slug: str,
    user_id: RequiredUserIdDep,
    article_svc: ArticleServiceDep,
):
    try:
        article_svc.delete(slug, user_id)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"body": ["Not Found"]}})
    except ForbiddenError:
        raise HTTPException(403, detail={"errors": {"body": ["Forbidden"]}})
    return {}


@router.post("/articles/{slug}/favorite")
def favorite_article(
    slug: str,
    user_id: RequiredUserIdDep,
    article_svc: ArticleServiceDep,
    profile_svc: ProfileServiceDep,
):
    try:
        article = article_svc.favorite(slug, user_id)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"body": ["Not Found"]}})
    return {"article": _resolve_article(article, article_svc, profile_svc, user_id)}


@router.delete("/articles/{slug}/favorite")
def unfavorite_article(
    slug: str,
    user_id: RequiredUserIdDep,
    article_svc: ArticleServiceDep,
    profile_svc: ProfileServiceDep,
):
    try:
        article = article_svc.unfavorite(slug, user_id)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"body": ["Not Found"]}})
    return {"article": _resolve_article(article, article_svc, profile_svc, user_id)}


@router.get("/tags")
def get_tags(article_svc: ArticleServiceDep):
    return {"tags": article_svc.all_tags()}
