"""Article routes for the API."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel

from app.domain.models import User
from app.schemas.article import (
    ArticleWrapper,
    ArticleListWrapper,
    ArticleListResponse,
    TagListWrapper,
    ArticleCreate,
    ArticleUpdate,
)
from app.use_cases.article_service import ArticleService
from app.adapters.database import SQLModelUserRepository, SQLModelArticleRepository
from app.database import get_session
from app.routes.auth import get_current_user, get_current_user_required

router = APIRouter(prefix="/api/articles", tags=["articles"])


def get_article_service(session = Depends(get_session)) -> ArticleService:
    """Get article service."""
    article_repo = SQLModelArticleRepository(session)
    return ArticleService(article_repo)


@router.post("", response_model=ArticleWrapper, status_code=201)
async def create_article(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """Create a new article."""
    article_data = ArticleCreate(**body.get("article", {}))
    article = await article_service.create_article(current_user, article_data)
    
    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tag_list": article.tag_list,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "favorited": False,
            "favorites_count": article.favorites_count,
            "author": {
                "username": current_user.username,
                "bio": current_user.bio,
                "image": current_user.image,
            },
        }
    )


@router.get("/{slug}", response_model=ArticleWrapper)
async def get_article(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user),
    article_service: ArticleService = Depends(get_article_service),
):
    """Get an article by slug."""
    user_id = current_user.id if current_user else None
    result = await article_service.get_article_by_slug(slug, user_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Article not found")
    
    article = result["article"]
    favorited = result["favorited"]
    
    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tag_list": article.tag_list,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "favorited": favorited,
            "favorites_count": article.favorites_count,
            "author": {
                "username": article.author.username,
                "bio": article.author.bio,
                "image": article.author.image,
            },
        }
    )


@router.put("/{slug}", response_model=ArticleWrapper)
async def update_article(
    slug: str,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """Update an article."""
    article_data = ArticleUpdate(**body.get("article", {}))
    
    try:
        article = await article_service.update_article(slug, current_user, article_data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tag_list": article.tag_list,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "favorited": False,
            "favorites_count": article.favorites_count,
            "author": {
                "username": article.author.username,
                "bio": article.author.bio,
                "image": article.author.image,
            },
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
        raise HTTPException(status_code=403, detail=str(e))
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return None


@router.get("", response_model=ArticleListWrapper)
async def list_articles(
    tag: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    favorited: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user),
    article_service: ArticleService = Depends(get_article_service),
):
    """List articles with filters."""
    user_id = current_user.id if current_user else None
    
    articles, total = await article_service.list_articles(
        tag=tag,
        author=author,
        favorited=favorited,
        limit=limit,
        offset=offset,
        current_user_id=user_id,
    )
    
    article_list = []
    for article in articles:
        favorited_by_user = False
        if user_id:
            # Check favorited status
            favorited_by_user = await article_service.article_repository.is_favorited(article.id, user_id)
        
        article_list.append({
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "tag_list": article.tag_list,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "favorited": favorited_by_user,
            "favorites_count": article.favorites_count,
            "author": {
                "username": article.author.username,
                "bio": article.author.bio,
                "image": article.author.image,
            },
        })
    
    return ArticleListWrapper(articles=article_list, articles_count=total)


@router.get("/feed", response_model=ArticleListWrapper)
async def get_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """Get feed of articles from followed users."""
    # Get follower IDs (simplified - need to implement follow functionality)
    follower_ids = []
    
    articles = await article_service.get_feed(follower_ids, limit, offset)
    
    article_list = []
    for article in articles:
        article_list.append({
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "tag_list": article.tag_list,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "favorited": False,
            "favorites_count": article.favorites_count,
            "author": {
                "username": article.author.username,
                "bio": article.author.bio,
                "image": article.author.image,
            },
        })
    
    return ArticleListWrapper(articles=article_list, articles_count=len(articles))


@router.post("/{slug}/favorite", response_model=ArticleWrapper)
async def favorite_article(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """Favorite an article."""
    article = await article_service.favorite_article(slug, current_user.id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tag_list": article.tag_list,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "favorited": True,
            "favorites_count": article.favorites_count,
            "author": {
                "username": article.author.username,
                "bio": article.author.bio,
                "image": article.author.image,
            },
        }
    )


@router.delete("/{slug}/favorite", response_model=ArticleWrapper)
async def unfavorite_article(
    slug: str,
    current_user: User = Depends(get_current_user_required),
    article_service: ArticleService = Depends(get_article_service),
):
    """Unfavorite an article."""
    article = await article_service.unfavorite_article(slug, current_user.id)
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return ArticleWrapper(
        article={
            "slug": article.slug,
            "title": article.title,
            "description": article.description,
            "body": article.body,
            "tag_list": article.tag_list,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "favorited": False,
            "favorites_count": article.favorites_count,
            "author": {
                "username": article.author.username,
                "bio": article.author.bio,
                "image": article.author.image,
            },
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
