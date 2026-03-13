"""Behavior: update user profile."""

import pytest

from app.use_cases.errors import (
    DuplicateEmailError,
    DuplicateUsernameError,
    ValidationError,
)
from app.use_cases.user_service import UserService
from tests.fakes import FakePasswordHasher, FakeTokenService, FakeUserRepository


def make_service() -> UserService:
    return UserService(FakeUserRepository(), FakePasswordHasher(), FakeTokenService())


def make_user(svc: UserService):
    user, _ = svc.register("alice", "alice@example.com", "s3cret")
    return user


def test_update_email():
    svc = make_service()
    user = make_user(svc)
    updated, _ = svc.update_user(user.id, email="new@example.com")
    assert updated.email == "new@example.com"


def test_update_username():
    svc = make_service()
    user = make_user(svc)
    updated, _ = svc.update_user(user.id, username="newname")
    assert updated.username == "newname"


def test_update_bio():
    svc = make_service()
    user = make_user(svc)
    updated, _ = svc.update_user(user.id, bio="A bio")
    assert updated.bio == "A bio"


def test_update_image():
    svc = make_service()
    user = make_user(svc)
    updated, _ = svc.update_user(user.id, image="https://example.com/photo.jpg")
    assert updated.image == "https://example.com/photo.jpg"


def test_update_bio_empty_string_normalizes_to_none():
    svc = make_service()
    user = make_user(svc)
    svc.update_user(user.id, bio="A bio")
    updated, _ = svc.update_user(user.id, bio="")
    assert updated.bio is None


def test_update_bio_whitespace_normalizes_to_none():
    svc = make_service()
    user = make_user(svc)
    updated, _ = svc.update_user(user.id, bio="   ")
    assert updated.bio is None


def test_update_bio_null_sets_none():
    svc = make_service()
    user = make_user(svc)
    svc.update_user(user.id, bio="A bio")
    updated, _ = svc.update_user(user.id, bio=None)
    assert updated.bio is None


def test_update_image_empty_string_normalizes_to_none():
    svc = make_service()
    user = make_user(svc)
    svc.update_user(user.id, image="https://example.com/p.jpg")
    updated, _ = svc.update_user(user.id, image="")
    assert updated.image is None


def test_update_image_null_sets_none():
    svc = make_service()
    user = make_user(svc)
    svc.update_user(user.id, image="https://example.com/p.jpg")
    updated, _ = svc.update_user(user.id, image=None)
    assert updated.image is None


def test_update_password_changes_hash():
    svc = make_service()
    user = make_user(svc)
    updated, _ = svc.update_user(user.id, password="newpass")
    assert updated.hashed_password == "hashed:newpass"


def test_update_returns_token():
    svc = make_service()
    user = make_user(svc)
    _, token = svc.update_user(user.id, bio="A bio")
    assert token.startswith("token:")


def test_update_blank_email_raises():
    svc = make_service()
    user = make_user(svc)
    with pytest.raises(ValidationError) as exc_info:
        svc.update_user(user.id, email="")
    assert exc_info.value.field == "email"


def test_update_blank_username_raises():
    svc = make_service()
    user = make_user(svc)
    with pytest.raises(ValidationError) as exc_info:
        svc.update_user(user.id, username="")
    assert exc_info.value.field == "username"


def test_update_null_email_raises():
    svc = make_service()
    user = make_user(svc)
    with pytest.raises(ValidationError):
        svc.update_user(user.id, email=None)  # type: ignore[arg-type]


def test_update_null_username_raises():
    svc = make_service()
    user = make_user(svc)
    with pytest.raises(ValidationError):
        svc.update_user(user.id, username=None)  # type: ignore[arg-type]


def test_update_duplicate_email_raises():
    svc = make_service()
    user = make_user(svc)
    svc.register("bob", "bob@example.com", "s3cret")
    with pytest.raises(DuplicateEmailError):
        svc.update_user(user.id, email="bob@example.com")


def test_update_duplicate_username_raises():
    svc = make_service()
    user = make_user(svc)
    svc.register("bob", "bob@example.com", "s3cret")
    with pytest.raises(DuplicateUsernameError):
        svc.update_user(user.id, username="bob")
