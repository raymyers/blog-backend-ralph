"""Behavior: login and get current user."""

import pytest

from app.use_cases.errors import InvalidCredentialsError, ValidationError
from app.use_cases.user_service import UserService
from tests.fakes import FakePasswordHasher, FakeTokenService, FakeUserRepository


def make_service() -> UserService:
    return UserService(FakeUserRepository(), FakePasswordHasher(), FakeTokenService())


def make_registered_user(svc: UserService):
    return svc.register("alice", "alice@example.com", "s3cret")


def test_login_returns_user():
    svc = make_service()
    make_registered_user(svc)
    user, _ = svc.login("alice@example.com", "s3cret")
    assert user.email == "alice@example.com"


def test_login_returns_token():
    svc = make_service()
    make_registered_user(svc)
    _, token = svc.login("alice@example.com", "s3cret")
    assert token.startswith("token:")


def test_login_wrong_password_raises():
    svc = make_service()
    make_registered_user(svc)
    with pytest.raises(InvalidCredentialsError):
        svc.login("alice@example.com", "wrongpassword")


def test_login_unknown_email_raises():
    svc = make_service()
    with pytest.raises(InvalidCredentialsError):
        svc.login("nobody@example.com", "s3cret")


def test_login_blank_email_raises_validation():
    svc = make_service()
    with pytest.raises(ValidationError) as exc_info:
        svc.login("", "s3cret")
    assert exc_info.value.field == "email"


def test_login_blank_password_raises_validation():
    svc = make_service()
    make_registered_user(svc)
    with pytest.raises(ValidationError) as exc_info:
        svc.login("alice@example.com", "")
    assert exc_info.value.field == "password"


def test_get_current_user_returns_user():
    svc = make_service()
    registered, _ = make_registered_user(svc)
    user, _ = svc.get_current_user(registered.id)
    assert user.email == "alice@example.com"


def test_get_current_user_returns_fresh_token():
    svc = make_service()
    registered, _ = make_registered_user(svc)
    _, token = svc.get_current_user(registered.id)
    assert token.startswith("token:")


def test_get_current_user_invalid_id_raises():
    svc = make_service()
    with pytest.raises(InvalidCredentialsError):
        svc.get_current_user(999)
