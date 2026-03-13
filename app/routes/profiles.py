from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_session
from app.domain.models import User
from app.routes.auth import get_current_user_optional, get_current_user_required
from app.use_cases.profile_service import ProfileService

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


class ProfileResponse(BaseModel):
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool


class ProfileWrapper(BaseModel):
    profile: ProfileResponse


def get_profile_service(session=Depends(get_session)) -> ProfileService:
    return ProfileService(session)


@router.get("/{username}", response_model=ProfileWrapper)
async def get_profile(
    username: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    svc: ProfileService = Depends(get_profile_service),
):
    profile = await svc.get_profile(username, current_user.id if current_user else None)
    if not profile:
        raise HTTPException(404, detail={"errors": {"profile": ["not found"]}})
    return ProfileWrapper(profile=profile)


@router.post("/{username}/follow", response_model=ProfileWrapper)
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user_required),
    svc: ProfileService = Depends(get_profile_service),
):
    profile = await svc.follow_user(username, current_user.id)
    if not profile:
        raise HTTPException(404, detail={"errors": {"profile": ["not found"]}})
    return ProfileWrapper(profile=profile)


@router.delete("/{username}/follow", response_model=ProfileWrapper)
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user_required),
    svc: ProfileService = Depends(get_profile_service),
):
    profile = await svc.unfollow_user(username, current_user.id)
    if not profile:
        raise HTTPException(404, detail={"errors": {"profile": ["not found"]}})
    return ProfileWrapper(profile=profile)
