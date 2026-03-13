from typing import List, Optional

from sqlmodel import Session, select

from app.adapters.database import SQLModelUserRepository
from app.domain.models import Follow


class ProfileService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.user_repo = SQLModelUserRepository(session)

    async def get_profile(self, username: str, current_user_id: Optional[int] = None) -> Optional[dict]:
        user = await self.user_repo.get_by_username(username)
        if not user:
            return None
        following = await self.is_following(current_user_id, user.id) if current_user_id else False
        return {"username": user.username, "bio": user.bio, "image": user.image, "following": following}

    async def follow_user(self, username: str, current_user_id: int) -> Optional[dict]:
        target = await self.user_repo.get_by_username(username)
        if not target:
            return None
        if target.id == current_user_id:
            raise ValueError("Cannot follow yourself")
        if not await self.is_following(current_user_id, target.id):
            self.session.add(Follow(follower_id=current_user_id, following_id=target.id))
            self.session.commit()
        return {"username": target.username, "bio": target.bio, "image": target.image, "following": True}

    async def unfollow_user(self, username: str, current_user_id: int) -> Optional[dict]:
        target = await self.user_repo.get_by_username(username)
        if not target:
            return None
        stmt = select(Follow).where(Follow.follower_id == current_user_id, Follow.following_id == target.id)
        follow = self.session.exec(stmt).first()
        if follow:
            self.session.delete(follow)
            self.session.commit()
        return {"username": target.username, "bio": target.bio, "image": target.image, "following": False}

    async def is_following(self, follower_id: int, following_id: int) -> bool:
        stmt = select(Follow).where(Follow.follower_id == follower_id, Follow.following_id == following_id)
        return self.session.exec(stmt).first() is not None

    async def get_following(self, user_id: int) -> List[int]:
        stmt = select(Follow.following_id).where(Follow.follower_id == user_id)
        return list(self.session.exec(stmt).all())
