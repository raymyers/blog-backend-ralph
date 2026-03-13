"""User service for authentication and profile management."""
from typing import Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.models import User
from app.schemas.user import UserCreate, UserUpdate
from app.ports.interfaces import UserRepository, PasswordHasher, TokenGenerator


class UserService:
    """Service for user operations."""
    
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_generator: TokenGenerator,
    ):
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_generator = token_generator
    
    async def register(self, user_data: UserCreate) -> tuple[User, str]:
        """Register a new user and return user with token."""
        # Check if email exists
        existing_email = await self.user_repository.get_by_email(user_data.email)
        if existing_email:
            raise ValueError("Email already registered")
        
        # Check if username exists
        existing_username = await self.user_repository.get_by_username(user_data.username)
        if existing_username:
            raise ValueError("Username already taken")
        
        # Create user
        password_hash = self.password_hasher.hash(user_data.password)
        user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=password_hash,
        )
        
        created_user = await self.user_repository.create(user)
        
        # Generate token
        token = self.token_generator.create_access_token(
            data={"sub": str(created_user.id), "email": created_user.email}
        )
        
        return created_user, token
    
    async def login(self, email: str, password: str) -> tuple[User, str]:
        """Login user and return user with token."""
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")
        
        if not self.password_hasher.verify(password, user.password_hash):
            raise ValueError("Invalid credentials")
        
        token = self.token_generator.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        return user, token
    
    async def get_current_user(self, user_id: int) -> Optional[User]:
        """Get current user by ID."""
        return await self.user_repository.get_by_id(user_id)
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user profile."""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Update fields if provided
        if user_data.email is not None:
            # Check if email is being changed to one that's already taken
            if user_data.email != user.email:
                existing = await self.user_repository.get_by_email(user_data.email)
                if existing and existing.id != user_id:
                    raise ValueError("Email already registered")
                # Reject empty or null email
                if not user_data.email.strip():
                    raise ValueError("email is required")
                user.email = user_data.email
        
        if user_data.username is not None:
            # Check if username is being changed to one that's already taken
            if user_data.username != user.username:
                existing = await self.user_repository.get_by_username(user_data.username)
                if existing and existing.id != user_id:
                    raise ValueError("Username already taken")
                # Reject empty or null username
                if not user_data.username.strip():
                    raise ValueError("username is required")
                user.username = user_data.username
        
        if user_data.password is not None:
            user.password_hash = self.password_hasher.hash(user_data.password)
        
        if user_data.bio is not None:
            # Empty string normalizes to null
            new_bio = user_data.bio if user_data.bio.strip() else None
            user.bio = new_bio
        
        if user_data.image is not None:
            # Empty string normalizes to null
            new_image = user_data.image if user_data.image.strip() else None
            user.image = new_image
        
        user.updated_at = datetime.utcnow()
        
        return await self.user_repository.update(user)
    
    async def generate_fresh_token(self, user: User) -> str:
        """Generate a fresh token for the current user."""
        return self.token_generator.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
