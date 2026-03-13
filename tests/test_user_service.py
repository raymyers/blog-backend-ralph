"""Tests for user service."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.use_cases.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.domain.models import User
from app.ports.interfaces import UserRepository, PasswordHasher, TokenGenerator


class MockUserRepository(UserRepository):
    """In-memory user repository for testing."""
    
    def __init__(self):
        self.users = {}
        self.next_id = 1
    
    async def create(self, user: User) -> User:
        user.id = self.next_id
        self.users[self.next_id] = user
        self.next_id += 1
        return user
    
    async def get_by_id(self, user_id: int) -> User:
        return self.users.get(user_id)
    
    async def get_by_email(self, email: str) -> User:
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    async def get_by_username(self, username: str) -> User:
        for user in self.users.values():
            if user.username == username:
                return user
        return None
    
    async def update(self, user: User) -> User:
        self.users[user.id] = user
        return user


class MockPasswordHasher(PasswordHasher):
    """In-memory password hasher for testing."""
    
    def hash(self, password: str) -> str:
        return f"hashed_{password}"
    
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return hashed_password == f"hashed_{plain_password}"


class MockTokenGenerator(TokenGenerator):
    """In-memory token generator for testing."""
    
    def create_access_token(self, data: dict) -> str:
        return f"token_for_{data.get('sub', 'unknown')}"
    
    def decode_token(self, token: str) -> dict:
        return {"sub": token.split("_")[-1]}


@pytest.fixture
def user_repository():
    return MockUserRepository()


@pytest.fixture
def password_hasher():
    return MockPasswordHasher()


@pytest.fixture
def token_generator():
    return MockTokenGenerator()


@pytest.fixture
def user_service(user_repository, password_hasher, token_generator):
    return UserService(user_repository, password_hasher, token_generator)


@pytest.mark.asyncio
async def test_register_success(user_service):
    """Test successful user registration."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )
    
    user, token = await user_service.register(user_data)
    
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert token == "token_for_1"


@pytest.mark.asyncio
async def test_register_duplicate_email(user_service):
    """Test registration fails with duplicate email."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )
    
    await user_service.register(user_data)
    
    # Try to register with same email
    user_data2 = UserCreate(
        email="test@example.com",
        username="otheruser",
        password="password456",
    )
    
    with pytest.raises(ValueError, match="Email already registered"):
        await user_service.register(user_data2)


@pytest.mark.asyncio
async def test_register_duplicate_username(user_service):
    """Test registration fails with duplicate username."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )
    
    await user_service.register(user_data)
    
    # Try to register with same username
    user_data2 = UserCreate(
        email="other@example.com",
        username="testuser",
        password="password456",
    )
    
    with pytest.raises(ValueError, match="Username already taken"):
        await user_service.register(user_data2)


@pytest.mark.asyncio
async def test_login_success(user_service):
    """Test successful login."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )
    
    await user_service.register(user_data)
    
    user, token = await user_service.login("test@example.com", "password123")
    
    assert user.email == "test@example.com"
    assert token == "token_for_1"


@pytest.mark.asyncio
async def test_login_invalid_email(user_service):
    """Test login fails with invalid email."""
    with pytest.raises(ValueError, match="Invalid credentials"):
        await user_service.login("nonexistent@example.com", "password123")


@pytest.mark.asyncio
async def test_login_invalid_password(user_service):
    """Test login fails with invalid password."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )
    
    await user_service.register(user_data)
    
    with pytest.raises(ValueError, match="Invalid credentials"):
        await user_service.login("test@example.com", "wrongpassword")


@pytest.mark.asyncio
async def test_update_user(user_service):
    """Test updating user profile."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )
    
    user, _ = await user_service.register(user_data)
    
    update_data = UserUpdate(
        bio="New bio",
        image="https://example.com/image.jpg",
    )
    
    updated_user = await user_service.update_user(user.id, update_data)
    
    assert updated_user.bio == "New bio"
    assert updated_user.image == "https://example.com/image.jpg"


@pytest.mark.asyncio
async def test_update_user_empty_bio_normalizes_to_null(user_service):
    """Test that empty bio normalizes to null."""
    user_data = UserCreate(
        email="test@example.com",
        username="testuser",
        password="password123",
    )
    
    user, _ = await user_service.register(user_data)
    
    update_data = UserUpdate(bio="")
    
    updated_user = await user_service.update_user(user.id, update_data)
    
    assert updated_user.bio is None
