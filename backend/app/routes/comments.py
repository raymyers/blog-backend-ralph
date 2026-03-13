from typing import Any

from fastapi import APIRouter, HTTPException

from app.deps import CommentServiceDep, OptionalUserIdDep, ProfileServiceDep, RequiredUserIdDep
from app.domain.models import Comment, User
from app.use_cases.errors import CommentNotFoundError, ForbiddenError, NotFoundError, ValidationError

router = APIRouter()


def _author_dict(user: User, following: bool) -> dict[str, Any]:
    return {
        "username": user.username,
        "bio": user.bio,
        "image": user.image,
        "following": following,
    }


def _comment_dict(comment: Comment, author: User, following: bool) -> dict[str, Any]:
    return {
        "id": comment.id,
        "createdAt": comment.created_at.isoformat().replace("+00:00", "Z"),
        "updatedAt": comment.updated_at.isoformat().replace("+00:00", "Z"),
        "body": comment.body,
        "author": _author_dict(author, following),
    }


def _resolve_comment(comment: Comment, profile_svc, viewer_id: int | None) -> dict[str, Any]:
    user = profile_svc._users.find_by_id(comment.author_id)
    if user is None:
        raise HTTPException(404, detail={"errors": {"body": ["Author not found"]}})
    following = (
        profile_svc._follows.is_following(viewer_id, user.id)
        if viewer_id and user.id
        else False
    )
    return _comment_dict(comment, user, following)


@router.post("/articles/{slug}/comments", status_code=201)
def add_comment(
    slug: str,
    body: dict[str, Any],
    user_id: RequiredUserIdDep,
    comment_svc: CommentServiceDep,
    profile_svc: ProfileServiceDep,
):
    data = body.get("comment", {})
    try:
        comment = comment_svc.add(slug, author_id=user_id, body=data.get("body", ""))
    except ValidationError as e:
        raise HTTPException(422, detail={"errors": {e.field: [e.message]}})
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"article": ["not found"]}})
    return {"comment": _resolve_comment(comment, profile_svc, user_id)}


@router.get("/articles/{slug}/comments")
def list_comments(
    slug: str,
    viewer_id: OptionalUserIdDep,
    comment_svc: CommentServiceDep,
    profile_svc: ProfileServiceDep,
):
    try:
        comments = comment_svc.list_for_article(slug)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"article": ["not found"]}})
    return {"comments": [_resolve_comment(c, profile_svc, viewer_id) for c in comments]}


@router.delete("/articles/{slug}/comments/{comment_id}", status_code=204)
def delete_comment(
    slug: str,
    comment_id: int,
    user_id: RequiredUserIdDep,
    comment_svc: CommentServiceDep,
):
    try:
        comment_svc.delete(slug, comment_id, user_id)
    except CommentNotFoundError:
        raise HTTPException(404, detail={"errors": {"comment": ["not found"]}})
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"article": ["not found"]}})
    except ForbiddenError:
        raise HTTPException(403, detail={"errors": {"comment": ["forbidden"]}})
    return None
