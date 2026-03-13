from app.domain.models import User
from app.ports.interfaces import FollowRepository, UserRepository
from app.use_cases.errors import NotFoundError


class ProfileService:
    def __init__(self, users: UserRepository, follows: FollowRepository) -> None:
        self._users = users
        self._follows = follows

    def get_profile(self, username: str, viewer_id: int | None = None) -> tuple[User, bool]:
        user = self._users.find_by_username(username)
        if user is None:
            raise NotFoundError(username)
        following = (
            self._follows.is_following(viewer_id, user.id)  # type: ignore[arg-type]
            if viewer_id is not None and user.id is not None
            else False
        )
        return user, following

    def follow(self, username: str, follower_id: int) -> tuple[User, bool]:
        user = self._users.find_by_username(username)
        if user is None:
            raise NotFoundError(username)
        assert user.id is not None
        self._follows.follow(follower_id, user.id)
        return user, True

    def unfollow(self, username: str, follower_id: int) -> tuple[User, bool]:
        user = self._users.find_by_username(username)
        if user is None:
            raise NotFoundError(username)
        assert user.id is not None
        self._follows.unfollow(follower_id, user.id)
        return user, False
