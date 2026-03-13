"""Profile service for user profiles and follow functionality."""
from typing import Optional, List
from sqlmodel import select

from app.domain.models import User, Follow
from app.adapters.database import SQLModelUserRepository
from app.database import Session


class ProfileService:
    """Service for profile operations."""
    
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = SQLModelUserRepository(session)
    
    async def get_profile(self, username: str, current_user_id: Optional[int] = None) -> Optional[dict]:
        """Get a user profile by username."""
        user = await self.user_repo.get_by_username(username)
        if not user:
            return None
        
        # Check if current user follows this profile
        following = False
        if current_user_id:
            following = await self.is_following(current_user_id, user.id)
        
        return {
            "username": user.username,
            "bio": user.bio,
            "image": user.image,
            "following": following,
        }
    
    async def follow_user(self, username: str, current_user_id: int) -> Optional[dict]:
        """Follow a user."""
        target_user = await self.user_repo.get_by_username(username)
        if not target_user:
            return None
        
        if target_user.id == current_user_id:
            # Can't follow yourself
            raise ValueError("Cannot follow yourself")
        
        # Check if already following
        if await self.is_following(current_user_id, target_user.id):
            # Already following, just return profile
            return {
                "username": target_user.username,
                "bio": target_user.bio,
                "image": target_user.image,
                "following": True,
            }
        
        # Create follow relationship
        follow = Follow(follower_id=current_user_id, following_id=target_user.id)
        self.session.add(follow)
        self.session.commit()
        
        return {
            "username": target_user.username,
            "bio": target_user.bio,
            "image": target_user.image,
            "following": True,
        }
    
    async def unfollow_user(self, username: str, current_user_id: int) -> Optional[dict]:
        """Unfollow a user."""
        target_user = await self.user_repo.get_by_username(username)
        if not target_user:
            return None
        
        # Remove follow relationship
        statement = select(Follow).where(
            Follow.follower_id == current_user_id,
            Follow.following_id == target_user.id
        )
        follow = self.session.exec(statement).first()
        if follow:
            self.session.delete(follow)
            self.session.commit()
        
        return {
            "username": target_user.username,
            "bio": target_user.bio,
            "image": target_user.image,
            "following": False,
        }
    
    async def is_following(self, follower_id: int, following_id: int) -> bool:
        """Check if follower_id is following following_id."""
        statement = select(Follow).where(
            Follow.follower_id == follower_id,
            Follow.following_id == following_id
        )
        return self.session.exec(statement).first() is not None
    
    async def get_followers(self, user_id: int) -> List[int]:
        """Get IDs of users following this user."""
        statement = select(Follow.follower_id).where(Follow.following_id == user_id)
        return list(self.session.exec(statement).all())
    
    async def get_following(self, user_id: int) -> List[int]:
        """Get IDs of users this user follows."""
        statement = select(Follow.following_id).where(Follow.follower_id == user_id)
        return list(self.session.exec(statement).all())
