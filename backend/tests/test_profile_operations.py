"""Behavior: get profile, follow, unfollow."""

import pytest

from app.use_cases.errors import NotFoundError
from app.use_cases.profile_service import ProfileService
from tests.fakes import FakeFollowRepository, FakeUserRepository


def make_service() -> tuple[ProfileService, FakeUserRepository]:
    users = FakeUserRepository()
    follows = FakeFollowRepository()
    svc = ProfileService(users, follows)
    return svc, users


def seed_user(users: FakeUserRepository, username: str = "alice") -> int:
    from app.domain.models import User
    u = users.create(User(email=f"{username}@example.com", username=username, hashed_password="x"))
    assert u.id is not None
    return u.id


def test_get_profile_returns_user():
    svc, users = make_service()
    seed_user(users, "alice")
    user, _ = svc.get_profile("alice")
    assert user.username == "alice"


def test_get_profile_not_following_by_default():
    svc, users = make_service()
    seed_user(users, "alice")
    _, following = svc.get_profile("alice", viewer_id=2)
    assert following is False


def test_get_profile_unknown_username_raises():
    svc, _ = make_service()
    with pytest.raises(NotFoundError):
        svc.get_profile("nobody")


def test_follow_returns_following_true():
    svc, users = make_service()
    alice_id = seed_user(users, "alice")
    bob_id = seed_user(users, "bob")
    _, following = svc.follow("alice", follower_id=bob_id)
    assert following is True


def test_follow_unknown_username_raises():
    svc, _ = make_service()
    with pytest.raises(NotFoundError):
        svc.follow("nobody", follower_id=1)


def test_get_profile_shows_following_true_after_follow():
    svc, users = make_service()
    alice_id = seed_user(users, "alice")
    bob_id = seed_user(users, "bob")
    svc.follow("alice", follower_id=bob_id)
    _, following = svc.get_profile("alice", viewer_id=bob_id)
    assert following is True


def test_unfollow_returns_following_false():
    svc, users = make_service()
    alice_id = seed_user(users, "alice")
    bob_id = seed_user(users, "bob")
    svc.follow("alice", follower_id=bob_id)
    _, following = svc.unfollow("alice", follower_id=bob_id)
    assert following is False


def test_unfollow_unknown_username_raises():
    svc, _ = make_service()
    with pytest.raises(NotFoundError):
        svc.unfollow("nobody", follower_id=1)


def test_get_profile_shows_following_false_after_unfollow():
    svc, users = make_service()
    alice_id = seed_user(users, "alice")
    bob_id = seed_user(users, "bob")
    svc.follow("alice", follower_id=bob_id)
    svc.unfollow("alice", follower_id=bob_id)
    _, following = svc.get_profile("alice", viewer_id=bob_id)
    assert following is False
