"""Comment routes for the API."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import ValidationError as PydanticValidationError

from app.domain.models import User
from app.schemas.comment import (
    CommentWrapper,
    CommentListWrapper,
    CommentCreate,
)
from app.use_cases.comment_service import CommentService
from app.adapters.database import SQLModelUserRepository
from app.database import get_session
from app.routes.auth import get_current_user, get_current_user_required

router = APIRouter(prefix="/api/articles", tags=["comments"])


def get_comment_service(session=Depends(get_session)) -> CommentService:
    """Get comment service."""
    return CommentService(session)


def _comment_response(comment, author: User, following: bool = False) -> dict:
    return {
        "id": comment.id,
        "body": comment.body,
        "createdAt": comment.created_at,
        "updatedAt": comment.updated_at,
        "author": {
            "username": author.username,
            "bio": author.bio,
            "image": author.image,
            "following": following,
        },
    }


@router.post("/{slug}/comments", response_model=CommentWrapper, status_code=201)
async def create_comment(
    slug: str,
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Create a comment on an article."""
    comment_body = body.get("comment", {}).get("body", "")
    if not comment_body or not str(comment_body).strip():
        raise HTTPException(status_code=422, detail={"errors": {"body": ["can't be blank"]}})

    try:
        comment = await comment_service.create_comment(slug, current_user, comment_body)
    except KeyError as e:
        field = str(e).strip("'")
        raise HTTPException(status_code=404, detail={"errors": {field: ["not found"]}})

    return CommentWrapper(comment=_comment_response(comment, current_user))


@router.get("/{slug}/comments", response_model=CommentListWrapper)
async def get_comments(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user),
    comment_service: CommentService = Depends(get_comment_service),
    session=Depends(get_session),
):
    """Get all comments for an article."""
    try:
        comments = await comment_service.get_comments(slug)
    except KeyError as e:
        field = str(e).strip("'")
        raise HTTPException(status_code=404, detail={"errors": {field: ["not found"]}})

    user_repo = SQLModelUserRepository(session)
    comment_list = []
    for comment in comments:
        author = await user_repo.get_by_id(comment.author_id)
        comment_list.append({
            "id": comment.id,
            "body": comment.body,
            "createdAt": comment.created_at,
            "updatedAt": comment.updated_at,
            "author": {
                "username": author.username if author else "unknown",
                "bio": author.bio if author else None,
                "image": author.image if author else None,
                "following": False,
            },
        })

    return CommentListWrapper(comments=comment_list)


@router.delete("/{slug}/comments/{comment_id}", status_code=204)
async def delete_comment(
    slug: str,
    comment_id: int,
    current_user: User = Depends(get_current_user_required),
    comment_service: CommentService = Depends(get_comment_service),
):
    """Delete a comment."""
    try:
        await comment_service.delete_comment(slug, comment_id, current_user.id)
    except KeyError as e:
        field = str(e).strip("'")
        raise HTTPException(status_code=404, detail={"errors": {field: ["not found"]}})
    except PermissionError:
        raise HTTPException(status_code=403, detail={"errors": {"comment": ["forbidden"]}})

    return None
