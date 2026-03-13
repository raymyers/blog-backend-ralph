"""Profile routes for the API."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.domain.models import User
from app.use_cases.profile_service import ProfileService
from app.database import get_session
from app.routes.auth import get_current_user, get_current_user_required
from pydantic import BaseModel

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def get_profile_service(session = Depends(get_session)) -> ProfileService:
    """Get profile service."""
    return ProfileService(session)


class ProfileResponse(BaseModel):
    """Profile response schema."""
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool


class ProfileWrapper(BaseModel):
    """Wrapper for profile response."""
    profile: ProfileResponse


@router.get("/{username}", response_model=ProfileWrapper)
async def get_profile(
    username: str,
    current_user: Optional[User] = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Get a user profile."""
    user_id = current_user.id if current_user else None
    profile = await profile_service.get_profile(username, user_id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ProfileWrapper(profile=profile)


@router.post("/{username}/follow", response_model=ProfileWrapper)
async def follow_user(
    username: str,
    current_user: User = Depends(get_current_user_required),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Follow a user."""
    try:
        profile = await profile_service.follow_user(username, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ProfileWrapper(profile=profile)


@router.delete("/{username}/follow", response_model=ProfileWrapper)
async def unfollow_user(
    username: str,
    current_user: User = Depends(get_current_user_required),
    profile_service: ProfileService = Depends(get_profile_service),
):
    """Unfollow a user."""
    profile = await profile_service.unfollow_user(username, current_user.id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return ProfileWrapper(profile=profile)
