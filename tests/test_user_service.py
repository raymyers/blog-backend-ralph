"""Unit tests for UserService."""
import pytest

from app.domain.models import User
from app.ports.interfaces import PasswordHasher, TokenGenerator, UserRepository
from app.schemas.user import UserCreate, UserUpdate
from app.use_cases.user_service import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    UserService,
)


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------

class InMemoryUserRepo(UserRepository):
    def __init__(self) -> None:
        self._store: dict = {}
        self._next_id = 1

    async def create(self, user: User) -> User:
        user.id = self._next_id
        self._store[self._next_id] = user
        self._next_id += 1
        return user

    async def get_by_id(self, user_id: int):
        return self._store.get(user_id)

    async def get_by_email(self, email: str):
        return next((u for u in self._store.values() if u.email == email), None)

    async def get_by_username(self, username: str):
        return next((u for u in self._store.values() if u.username == username), None)

    async def update(self, user: User) -> User:
        self._store[user.id] = user
        return user


class FakeHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


class FakeTokenGen(TokenGenerator):
    def create_access_token(self, data: dict) -> str:
        return f"token-{data.get('sub', '?')}"

    def decode_token(self, token: str) -> dict:
        return {"sub": token.split("-")[-1]}


def make_service() -> UserService:
    return UserService(InMemoryUserRepo(), FakeHasher(), FakeTokenGen())


def make_user_data(**kwargs) -> UserCreate:
    defaults = {"email": "alice@example.com", "username": "alice", "password": "secret42"}
    return UserCreate(**{**defaults, **kwargs})


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_creates_user_with_token():
    svc = make_service()
    user, token = await svc.register(make_user_data())
    assert user.email == "alice@example.com"
    assert user.username == "alice"
    assert token == "token-1"


@pytest.mark.asyncio
async def test_register_hashes_password():
    svc = make_service()
    user, _ = await svc.register(make_user_data(password="secret42"))
    assert user.password_hash == "hashed:secret42"


@pytest.mark.asyncio
async def test_register_duplicate_email_raises():
    svc = make_service()
    await svc.register(make_user_data())
    with pytest.raises(DuplicateEmailError):
        await svc.register(make_user_data(username="bob"))


@pytest.mark.asyncio
async def test_register_duplicate_username_raises():
    svc = make_service()
    await svc.register(make_user_data())
    with pytest.raises(DuplicateUsernameError):
        await svc.register(make_user_data(email="bob@example.com"))


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_returns_user_and_token():
    svc = make_service()
    await svc.register(make_user_data())
    user, token = await svc.login("alice@example.com", "secret42")
    assert user.email == "alice@example.com"
    assert token == "token-1"


@pytest.mark.asyncio
async def test_login_wrong_email_raises():
    svc = make_service()
    with pytest.raises(InvalidCredentialsError):
        await svc.login("nobody@example.com", "secret42")


@pytest.mark.asyncio
async def test_login_wrong_password_raises():
    svc = make_service()
    await svc.register(make_user_data())
    with pytest.raises(InvalidCredentialsError):
        await svc.login("alice@example.com", "wrongpassword")


# ---------------------------------------------------------------------------
# update_user
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_user_bio_and_image():
    svc = make_service()
    user, _ = await svc.register(make_user_data())
    updated = await svc.update_user(user.id, UserUpdate(bio="A bio", image="https://img.example.com/a.png"))
    assert updated.bio == "A bio"
    assert updated.image == "https://img.example.com/a.png"


@pytest.mark.asyncio
async def test_update_user_empty_bio_normalizes_to_null():
    svc = make_service()
    user, _ = await svc.register(make_user_data())
    updated = await svc.update_user(user.id, UserUpdate(bio=""))
    assert updated.bio is None


@pytest.mark.asyncio
async def test_update_user_duplicate_email_raises():
    svc = make_service()
    await svc.register(make_user_data())
    bob_data = make_user_data(email="bob@example.com", username="bob")
    bob, _ = await svc.register(bob_data)
    with pytest.raises(DuplicateEmailError):
        await svc.update_user(bob.id, UserUpdate(email="alice@example.com"))
