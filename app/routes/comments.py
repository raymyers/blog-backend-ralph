"""Comment routes for the API."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body

from app.domain.models import User
from app.schemas.comment import (
    CommentWrapper,
    CommentListWrapper,
    CommentCreate,
)
from app.use_cases.comment_service import CommentService
from app.database import get_session
from app.routes.auth import get_current_user, get_current_user_required

router = APIRouter(prefix="/api/articles", tags=["comments"])


def get_comment_service(session = Depends(get_session)) -> CommentService:
    """Get comment service."""
    return CommentService(session)


@router.post("/{slug}/comments", response_model=CommentWrapper, status_code=201)
async def create_comment(
    slug: str,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Create a comment on an article."""
    comment_data = CommentCreate(**body.get("comment", {}))
    
    comment = await comment_service.create_comment(slug, current_user, comment_data.body)
    
    if not comment:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return CommentWrapper(comment={
        "id": comment.id,
        "body": comment.body,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "author": {
            "username": current_user.username,
            "bio": current_user.bio,
            "image": current_user.image,
        },
    })


@router.get("/{slug}/comments", response_model=CommentListWrapper)
async def get_comments(
    slug: str,
    current_user: User = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Get all comments for an article."""
    comments = await comment_service.get_comments(slug)
    
    # Get author info for each comment
    comment_list = []
    user_repo = None
    if comments:
        from app.adapters.database import SQLModelUserRepository
        user_repo = SQLModelUserRepository(comment_service.session)
    
    for comment in comments:
        author = await user_repo.get_by_id(comment.author_id) if user_repo else None
        comment_list.append({
            "id": comment.id,
            "body": comment.body,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "author": {
                "username": author.username if author else "unknown",
                "bio": author.bio if author else None,
                "image": author.image if author else None,
            },
        })
    
    return CommentListWrapper(comments=comment_list)


@router.delete("/{slug}/comments/{id}", status_code=204)
async def delete_comment(
    slug: str,
    id: int,
    current_user: User = Depends(get_current_user_required),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Delete a comment."""
    deleted = await comment_service.delete_comment(slug, id, current_user.id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    return None
