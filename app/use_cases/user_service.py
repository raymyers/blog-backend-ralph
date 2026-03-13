from datetime import datetime
from typing import Optional

from app.domain.models import User
from app.ports.interfaces import PasswordHasher, TokenGenerator, UserRepository
from app.schemas.user import UserCreate, UserUpdate


class DuplicateEmailError(Exception):
    pass


class DuplicateUsernameError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserService:
    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_generator: TokenGenerator,
    ) -> None:
        self.user_repository = user_repository
        self.password_hasher = password_hasher
        self.token_generator = token_generator

    async def register(self, user_data: UserCreate) -> tuple[User, str]:
        if await self.user_repository.get_by_email(user_data.email):
            raise DuplicateEmailError()
        if await self.user_repository.get_by_username(user_data.username):
            raise DuplicateUsernameError()

        user = User(
            email=user_data.email,
            username=user_data.username,
            password_hash=self.password_hasher.hash(user_data.password),
        )
        created = await self.user_repository.create(user)
        token = self.token_generator.create_access_token({"sub": str(created.id), "email": created.email})
        return created, token

    async def login(self, email: str, password: str) -> tuple[User, str]:
        user = await self.user_repository.get_by_email(email)
        if not user or not self.password_hasher.verify(password, user.password_hash):
            raise InvalidCredentialsError()
        token = self.token_generator.create_access_token({"sub": str(user.id), "email": user.email})
        return user, token

    async def get_current_user(self, user_id: int) -> Optional[User]:
        return await self.user_repository.get_by_id(user_id)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if user_data.email is not None:
            if user_data.email != user.email:
                if await self.user_repository.get_by_email(user_data.email):
                    raise DuplicateEmailError()
            user.email = user_data.email

        if user_data.username is not None:
            if user_data.username != user.username:
                if await self.user_repository.get_by_username(user_data.username):
                    raise DuplicateUsernameError()
            user.username = user_data.username

        if user_data.password is not None:
            user.password_hash = self.password_hasher.hash(user_data.password)

        if "bio" in user_data.model_fields_set:
            user.bio = user_data.bio if (user_data.bio and user_data.bio.strip()) else None

        if "image" in user_data.model_fields_set:
            user.image = user_data.image if (user_data.image and user_data.image.strip()) else None

        user.updated_at = datetime.utcnow()
        return await self.user_repository.update(user)

    async def generate_fresh_token(self, user: User) -> str:
        return self.token_generator.create_access_token({"sub": str(user.id), "email": user.email})
