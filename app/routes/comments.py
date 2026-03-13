from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException

from app.adapters.database import SQLModelUserRepository
from app.database import get_session
from app.domain.models import User
from app.routes.auth import get_current_user_optional, get_current_user_required
from app.schemas.comment import CommentListWrapper, CommentWrapper
from app.use_cases.comment_service import CommentService

router = APIRouter(prefix="/api/articles", tags=["comments"])


def get_comment_service(session=Depends(get_session)) -> CommentService:
    return CommentService(session)


def _comment_dict(comment, author: User, following: bool = False) -> dict:
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
    svc: CommentService = Depends(get_comment_service),
):
    comment_body = body.get("comment", {}).get("body", "")
    if not comment_body or not str(comment_body).strip():
        raise HTTPException(422, detail={"errors": {"body": ["can't be blank"]}})
    try:
        comment = await svc.create_comment(slug, current_user, comment_body)
    except KeyError as e:
        raise HTTPException(404, detail={"errors": {str(e).strip("'"): ["not found"]}})
    return CommentWrapper(comment=_comment_dict(comment, current_user))


@router.get("/{slug}/comments", response_model=CommentListWrapper)
async def get_comments(
    slug: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    svc: CommentService = Depends(get_comment_service),
    session=Depends(get_session),
):
    try:
        comments = await svc.get_comments(slug)
    except KeyError as e:
        raise HTTPException(404, detail={"errors": {str(e).strip("'"): ["not found"]}})
    user_repo = SQLModelUserRepository(session)
    comment_list = []
    for c in comments:
        author = await user_repo.get_by_id(c.author_id)
        if author:
            comment_list.append(_comment_dict(c, author))
    return CommentListWrapper(comments=comment_list)


@router.delete("/{slug}/comments/{comment_id}", status_code=204)
async def delete_comment(
    slug: str,
    comment_id: int,
    current_user: User = Depends(get_current_user_required),
    svc: CommentService = Depends(get_comment_service),
):
    try:
        await svc.delete_comment(slug, comment_id, current_user.id)
    except KeyError as e:
        raise HTTPException(404, detail={"errors": {str(e).strip("'"): ["not found"]}})
    except PermissionError:
        raise HTTPException(403, detail={"errors": {"comment": ["forbidden"]}})
    return None
