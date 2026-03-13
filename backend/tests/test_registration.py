"""Behavior: user registration."""

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


def test_register_returns_user_with_assigned_id():
    svc = make_service()
    user, _ = svc.register("alice", "alice@example.com", "s3cret")
    assert user.id is not None


def test_register_stores_email():
    svc = make_service()
    user, _ = svc.register("alice", "alice@example.com", "s3cret")
    assert user.email == "alice@example.com"


def test_register_stores_username():
    svc = make_service()
    user, _ = svc.register("alice", "alice@example.com", "s3cret")
    assert user.username == "alice"


def test_register_returns_jwt_token():
    svc = make_service()
    _, token = svc.register("alice", "alice@example.com", "s3cret")
    assert token.startswith("token:")


def test_register_hashes_password():
    svc = make_service()
    user, _ = svc.register("alice", "alice@example.com", "s3cret")
    assert user.hashed_password == "hashed:s3cret"


def test_register_bio_is_none_by_default():
    svc = make_service()
    user, _ = svc.register("alice", "alice@example.com", "s3cret")
    assert user.bio is None


def test_register_image_is_none_by_default():
    svc = make_service()
    user, _ = svc.register("alice", "alice@example.com", "s3cret")
    assert user.image is None


def test_register_blank_username_raises_validation_error():
    svc = make_service()
    with pytest.raises(ValidationError) as exc_info:
        svc.register("", "alice@example.com", "s3cret")
    assert exc_info.value.field == "username"


def test_register_blank_email_raises_validation_error():
    svc = make_service()
    with pytest.raises(ValidationError) as exc_info:
        svc.register("alice", "", "s3cret")
    assert exc_info.value.field == "email"


def test_register_blank_password_raises_validation_error():
    svc = make_service()
    with pytest.raises(ValidationError) as exc_info:
        svc.register("alice", "alice@example.com", "")
    assert exc_info.value.field == "password"


def test_register_duplicate_email_raises():
    svc = make_service()
    svc.register("alice", "alice@example.com", "s3cret")
    with pytest.raises(DuplicateEmailError):
        svc.register("other", "alice@example.com", "s3cret")


def test_register_duplicate_username_raises():
    svc = make_service()
    svc.register("alice", "alice@example.com", "s3cret")
    with pytest.raises(DuplicateUsernameError):
        svc.register("alice", "other@example.com", "s3cret")
