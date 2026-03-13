"""Article routes for the API."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import ValidationError as PydanticValidationError

from app.domain.models import User
from app.schemas.article import (
    ArticleWrapper,
    ArticleListWrapper,
    TagListWrapper,
    ArticleCreate,
    ArticleUpdate,
)
from app.use_cases.article_service import ArticleService
from app.use_cases.profile_service import ProfileService
from app.adapters.database import SQLModelUserRepository, SQLModelArticleRepository
from app.database import get_session
from app.routes.auth import get_current_user, get_current_user_required

router = APIRouter(prefix="/api/articles", tags=["articles"])


def get_article_service(session=Depends(get_session)) -> ArticleService:
    """Get article service."""
    article_repo = SQLModelArticleRepository(session)
    return ArticleService(article_repo)


def _build_author_profile(author: User, following: bool = False) -> dict:
    return {
        "username": author.username,
        "bio": author.bio,
        "image": author.image,
        "following": following,
    }



def _pydantic_error_to_http(exc: PydanticValidationError, status_code: int = 422) -> HTTPException:
    errors = {}
    for error in exc.errors():
        loc = error.get('loc', [])
        field = str(loc[-1]) if loc else 'body'
        msg_raw = error.get('msg', 'is invalid')
        if msg_raw.startswith('Value error, '):
            msg = msg_raw[len('Value error, '):]
        elif error.get('type') in ('string_too_short', 'missing'):
            msg = "can't be blank"
        else:
            msg = msg_raw
        if field not in errors:
            errors[field] = []
        errors[field].append(msg)
    return HTTPException(status_code=status_code, detail={'errors': errors})

# /feed must be declared BEFORE /{slug} to avoid route shadowing

@router.get("/feed", response_model=ArticleListWrapper)
async def get_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    """Get feed of articles from followed users."""
    profile_service = ProfileService(session)
    following_ids = await profile_service.get_following(current_user.id)

    articles = await article_service.get_feed(following_ids, limit, offset)
    total = await article_service.count_feed(following_ids)

    article_list = []
    for article in articles:
        favorited = await article_service.article_repository.is_favorited(article.id, current_user.id)
        following = await profile_service.is_following(current_user.id, article.author_id)
        article_list.append({
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "tagList": article.tag_list,
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "favorited": favorited,
            "favoritesCount": article.favorites_count,
            "author": _build_author_profile(article.author, following),
        })

    return ArticleListWrapper(articles=article_list, articlesCount=total)


@router.get("", response_model=ArticleListWrapper)
async def list_articles(
    tag: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    favorited: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user),
    article_service: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    """List articles with filters."""
    user_id = current_user.id if current_user else None

    author_id: Optional[int] = None
    if author:
        user_repo = SQLModelUserRepository(session)
        author_user = await user_repo.get_by_username(author)
        if author_user:
            author_id = author_user.id
        else:
            return ArticleListWrapper(articles=[], articlesCount=0)

    # Get total count (separate from paginated results)
    article_repo = article_service.article_repository
    if tag:
        total = await article_repo.count_by_tag(tag)
    elif author_id is not None:
        total = await article_repo.count_by_author(author_id)
    elif favorited:
        total = await article_repo.count_favorited_by(favorited)
    else:
        total = await article_repo.count_all()

    articles, _ = await article_service.list_articles(
        tag=tag,
        author_id=author_id,
        favorited=favorited,
        limit=limit,
        offset=offset,
        current_user_id=user_id,
    )

    profile_service = ProfileService(session)
    article_list = []
    for article in articles:
        favorited_by_user = False
        following = False
        if user_id:
            favorited_by_user = await article_service.article_repository.is_favorited(article.id, user_id)
            following = await profile_service.is_following(user_id, article.author_id)

        article_list.append({
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "tagList": article.tag_list,
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "favorited": favorited_by_user,
            "favoritesCount": article.favorites_count,
            "author": _build_author_profile(article.author, following),
        })

    return ArticleListWrapper(articles=article_list, articlesCount=total)


@router.post("", response_model=ArticleWrapper, status_code=201)
async def create_article(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """Create a new article."""
    try:
        article_data = ArticleCreate(**body.get("article", {}))
    except PydanticValidationError as exc:
        raise _pydantic_error_to_http(exc)
    article = await article_service.create_article(current_user, article_data)

    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tagList": article.tag_list,
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "favorited": False,
            "favoritesCount": article.favorites_count,
            "author": _build_author_profile(current_user),
        }
    )


@router.get("/{slug}", response_model=ArticleWrapper)
async def get_article(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user),
    article_service: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    """Get an article by slug."""
    user_id = current_user.id if current_user else None
    result = await article_service.get_article_by_slug(slug, user_id)

    if not result:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    article = result["article"]
    favorited = result["favorited"]

    following = False
    if current_user:
        profile_service = ProfileService(session)
        following = await profile_service.is_following(current_user.id, article.author_id)

    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tagList": article.tag_list,
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "favorited": favorited,
            "favoritesCount": article.favorites_count,
            "author": _build_author_profile(article.author, following),
        }
    )


@router.put("/{slug}", response_model=ArticleWrapper)
async def update_article(
    slug: str,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    """Update an article."""
    try:
        article_data = ArticleUpdate(**body.get("article", {}))
    except PydanticValidationError as exc:
        raise _pydantic_error_to_http(exc)

    try:
        article = await article_service.update_article(slug, current_user, article_data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail={"errors": {"article": ["forbidden"]}})

    if not article:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    favorited = await article_service.article_repository.is_favorited(article.id, current_user.id)
    profile_service = ProfileService(session)
    following = await profile_service.is_following(current_user.id, article.author_id)

    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tagList": article.tag_list,
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "favorited": favorited,
            "favoritesCount": article.favorites_count,
            "author": _build_author_profile(article.author, following),
        }
    )


@router.delete("/{slug}", status_code=204)
async def delete_article(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """Delete an article."""
    try:
        deleted = await article_service.delete_article(slug, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail={"errors": {"article": ["forbidden"]}})

    if not deleted:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    return None


@router.post("/{slug}/favorite", response_model=ArticleWrapper)
async def favorite_article(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    """Favorite an article."""
    article = await article_service.favorite_article(slug, current_user.id)

    if not article:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    profile_service = ProfileService(session)
    following = await profile_service.is_following(current_user.id, article.author_id)

    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tagList": article.tag_list,
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "favorited": True,
            "favoritesCount": article.favorites_count,
            "author": _build_author_profile(article.author, following),
        }
    )


@router.delete("/{slug}/favorite", response_model=ArticleWrapper)
async def unfavorite_article(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
    session=Depends(get_session),
):
    """Unfavorite an article."""
    article = await article_service.unfavorite_article(slug, current_user.id)

    if not article:
        raise HTTPException(status_code=404, detail={"errors": {"article": ["not found"]}})

    profile_service = ProfileService(session)
    following = await profile_service.is_following(current_user.id, article.author_id)

    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tagList": article.tag_list,
            "createdAt": article.created_at,
            "updatedAt": article.updated_at,
            "favorited": False,
            "favoritesCount": article.favorites_count,
            "author": _build_author_profile(article.author, following),
        }
    )


# Tags endpoint - separate router
tags_router = APIRouter(prefix="/api", tags=["tags"])


@tags_router.get("/tags", response_model=TagListWrapper)
async def get_tags(
    article_service: ArticleService = Depends(get_article_service),
):
    """Get all tags."""
    tags = await article_service.get_all_tags()
    return TagListWrapper(tags=tags)
