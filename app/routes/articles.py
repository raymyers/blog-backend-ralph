from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import ValidationError as PydanticValidationError

from app.adapters.database import SQLModelArticleRepository, SQLModelUserRepository
from app.database import get_session
from app.domain.models import User
from app.routes.auth import get_current_user_optional, get_current_user_required
from app.schemas.article import (
    ArticleCreate,
    ArticleListWrapper,
    ArticleUpdate,
    ArticleWrapper,
    TagListWrapper,
)
from app.use_cases.article_service import ArticleService
from app.use_cases.profile_service import ProfileService

router = APIRouter(prefix="/api/articles", tags=["articles"])
tags_router = APIRouter(prefix="/api", tags=["tags"])


def get_article_service(session=Depends(get_session)) -> ArticleService:
    return ArticleService(SQLModelArticleRepository(session))


def _author_dict(author: User, following: bool = False) -> dict:
    return {"username": author.username, "bio": author.bio, "image": author.image, "following": following}


def _pydantic_to_http(exc: PydanticValidationError) -> HTTPException:
    errors: dict = {}
    for error in exc.errors():
        loc = error.get("loc", [])
        field = str(loc[-1]) if loc else "body"
        msg = error.get("msg", "is invalid")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, "):]
        elif error.get("type") in ("string_too_short", "missing"):
            msg = "can't be blank"
        errors.setdefault(field, []).append(msg)
    return HTTPException(422, detail={"errors": errors})


# /feed MUST come before /{slug}
@router.get("/feed", response_model=ArticleListWrapper)
async def get_feed(
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_required),
    svc: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    profile_svc = ProfileService(session)
    following_ids = await profile_svc.get_following(current_user.id)
    articles = await svc.get_feed(following_ids, limit, offset)
    total = await svc.article_repository.count_feed(following_ids)

    items = []
    for a in articles:
        favorited = await svc.article_repository.is_favorited(a.id, current_user.id)
        following = await profile_svc.is_following(current_user.id, a.author_id)
        items.append({
            "slug": a.slug, "title": a.title, "description": a.description,
            "tagList": a.tag_list, "createdAt": a.created_at, "updatedAt": a.updated_at,
            "favorited": favorited, "favoritesCount": a.favorites_count,
            "author": _author_dict(a.author, following),
        })
    return ArticleListWrapper(articles=items, articlesCount=total)


@router.get("", response_model=ArticleListWrapper)
async def list_articles(
    tag: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    favorited: Optional[str] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user_optional),
    svc: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    user_id = current_user.id if current_user else None
    repo = svc.article_repository

    author_id: Optional[int] = None
    if author:
        author_user = await SQLModelUserRepository(session).get_by_username(author)
        if not author_user:
            return ArticleListWrapper(articles=[], articlesCount=0)
        author_id = author_user.id

    if tag:
        total = await repo.count_by_tag(tag)
    elif author_id is not None:
        total = await repo.count_by_author(author_id)
    elif favorited:
        total = await repo.count_favorited_by(favorited)
    else:
        total = await repo.count_all()

    articles = await svc.list_articles(tag=tag, author_id=author_id, favorited=favorited, limit=limit, offset=offset)

    profile_svc = ProfileService(session)
    items = []
    for a in articles:
        fav = await repo.is_favorited(a.id, user_id) if user_id else False
        following = await profile_svc.is_following(user_id, a.author_id) if user_id else False
        items.append({
            "slug": a.slug, "title": a.title, "description": a.description,
            "tagList": a.tag_list, "createdAt": a.created_at, "updatedAt": a.updated_at,
            "favorited": fav, "favoritesCount": a.favorites_count,
            "author": _author_dict(a.author, following),
        })
    return ArticleListWrapper(articles=items, articlesCount=total)


@router.post("", response_model=ArticleWrapper, status_code=201)
async def create_article(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    svc: ArticleService = Depends(get_article_service),
):
    try:
        data = ArticleCreate(**body.get("article", {}))
    except PydanticValidationError as exc:
        raise _pydantic_to_http(exc)
    article = await svc.create_article(current_user, data)
    return ArticleWrapper(article={
        "slug": article.slug, "title": article.title, "description": article.description,
        "body": article.body, "tagList": article.tag_list,
        "createdAt": article.created_at, "updatedAt": article.updated_at,
        "favorited": False, "favoritesCount": article.favorites_count,
        "author": _author_dict(current_user),
    })


@router.get("/{slug}", response_model=ArticleWrapper)
async def get_article(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    svc: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    result = await svc.get_article_by_slug(slug, current_user.id if current_user else None)
    if not result:
        raise HTTPException(404, detail={"errors": {"article": ["not found"]}})
    article = result["article"]
    following = False
    if current_user:
        following = await ProfileService(session).is_following(current_user.id, article.author_id)
    return ArticleWrapper(article={
        "slug": article.slug, "title": article.title, "description": article.description,
        "body": article.body, "tagList": article.tag_list,
        "createdAt": article.created_at, "updatedAt": article.updated_at,
        "favorited": result["favorited"], "favoritesCount": article.favorites_count,
        "author": _author_dict(article.author, following),
    })


@router.put("/{slug}", response_model=ArticleWrapper)
async def update_article(
    slug: str,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    svc: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    try:
        data = ArticleUpdate(**body.get("article", {}))
    except PydanticValidationError as exc:
        raise _pydantic_to_http(exc)
    try:
        article = await svc.update_article(slug, current_user, data)
    except PermissionError:
        raise HTTPException(403, detail={"errors": {"article": ["forbidden"]}})
    if not article:
        raise HTTPException(404, detail={"errors": {"article": ["not found"]}})
    favorited = await svc.article_repository.is_favorited(article.id, current_user.id)
    following = await ProfileService(session).is_following(current_user.id, article.author_id)
    return ArticleWrapper(article={
        "slug": article.slug, "title": article.title, "description": article.description,
        "body": article.body, "tagList": article.tag_list,
        "createdAt": article.created_at, "updatedAt": article.updated_at,
        "favorited": favorited, "favoritesCount": article.favorites_count,
        "author": _author_dict(article.author, following),
    })


@router.delete("/{slug}", status_code=204)
async def delete_article(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    svc: ArticleService = Depends(get_article_service),
):
    try:
        deleted = await svc.delete_article(slug, current_user)
    except PermissionError:
        raise HTTPException(403, detail={"errors": {"article": ["forbidden"]}})
    if not deleted:
        raise HTTPException(404, detail={"errors": {"article": ["not found"]}})
    return None


@router.post("/{slug}/favorite", response_model=ArticleWrapper)
async def favorite_article(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    svc: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    article = await svc.favorite_article(slug, current_user.id)
    if not article:
        raise HTTPException(404, detail={"errors": {"article": ["not found"]}})
    following = await ProfileService(session).is_following(current_user.id, article.author_id)
    return ArticleWrapper(article={
        "slug": article.slug, "title": article.title, "description": article.description,
        "body": article.body, "tagList": article.tag_list,
        "createdAt": article.created_at, "updatedAt": article.updated_at,
        "favorited": True, "favoritesCount": article.favorites_count,
        "author": _author_dict(article.author, following),
    })


@router.delete("/{slug}/favorite", response_model=ArticleWrapper)
async def unfavorite_article(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    svc: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    article = await svc.unfavorite_article(slug, current_user.id)
    if not article:
        raise HTTPException(404, detail={"errors": {"article": ["not found"]}})
    following = await ProfileService(session).is_following(current_user.id, article.author_id)
    return ArticleWrapper(article={
        "slug": article.slug, "title": article.title, "description": article.description,
        "body": article.body, "tagList": article.tag_list,
        "createdAt": article.created_at, "updatedAt": article.updated_at,
        "favorited": False, "favoritesCount": article.favorites_count,
        "author": _author_dict(article.author, following),
    })


@tags_router.get("/tags", response_model=TagListWrapper)
async def get_tags(svc: ArticleService = Depends(get_article_service)):
    return TagListWrapper(tags=await svc.get_all_tags())
