from typing import Any

from fastapi import APIRouter, HTTPException

from app.deps import OptionalUserIdDep, ProfileServiceDep, RequiredUserIdDep
from app.domain.models import User
from app.use_cases.errors import NotFoundError

router = APIRouter()


def _profile_response(user: User, following: bool) -> dict[str, Any]:
    return {
        "profile": {
            "username": user.username,
            "bio": user.bio,
            "image": user.image,
            "following": following,
        }
    }


@router.get("/profiles/{username}")
def get_profile(username: str, viewer_id: OptionalUserIdDep, svc: ProfileServiceDep):
    try:
        user, following = svc.get_profile(username, viewer_id)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"body": ["Not Found"]}})
    return _profile_response(user, following)


@router.post("/profiles/{username}/follow")
def follow_user(username: str, user_id: RequiredUserIdDep, svc: ProfileServiceDep):
    try:
        user, following = svc.follow(username, user_id)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"body": ["Not Found"]}})
    return _profile_response(user, following)


@router.delete("/profiles/{username}/follow")
def unfollow_user(username: str, user_id: RequiredUserIdDep, svc: ProfileServiceDep):
    try:
        user, following = svc.unfollow(username, user_id)
    except NotFoundError:
        raise HTTPException(404, detail={"errors": {"body": ["Not Found"]}})
    return _profile_response(user, following)
