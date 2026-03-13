from dataclasses import replace
from typing import Any

from app.domain.models import User
from app.ports.interfaces import PasswordHasher, TokenService, UserRepository
from app.use_cases.errors import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    ValidationError,
)

_UNSET: Any = object()  # sentinel: field was not provided in the update payload


class UserService:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens

    def register(self, username: str, email: str, password: str) -> tuple[User, str]:
        if not username.strip():
            raise ValidationError("username", "can't be blank")
        if not email.strip():
            raise ValidationError("email", "can't be blank")
        if not password.strip():
            raise ValidationError("password", "can't be blank")

        if self._users.find_by_email(email):
            raise DuplicateEmailError(email)
        if self._users.find_by_username(username):
            raise DuplicateUsernameError(username)

        user = self._users.create(
            User(
                email=email,
                username=username,
                hashed_password=self._hasher.hash(password),
            )
        )
        assert user.id is not None
        return user, self._tokens.create(user.id)

    def login(self, email: str, password: str) -> tuple[User, str]:
        if not email.strip():
            raise ValidationError("email", "can't be blank")
        if not password.strip():
            raise ValidationError("password", "can't be blank")

        user = self._users.find_by_email(email)
        if user is None or not self._hasher.verify(password, user.hashed_password):
            raise InvalidCredentialsError()

        assert user.id is not None
        return user, self._tokens.create(user.id)

    def get_current_user(self, user_id: int) -> tuple[User, str]:
        user = self._users.find_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError()
        assert user.id is not None
        return user, self._tokens.create(user.id)

    def update_user(
        self,
        user_id: int,
        *,
        email: Any = _UNSET,
        username: Any = _UNSET,
        password: str | None = None,
        bio: Any = _UNSET,
        image: Any = _UNSET,
    ) -> tuple[User, str]:
        user = self._users.find_by_id(user_id)
        if user is None:
            raise InvalidCredentialsError()

        if email is not _UNSET:
            if email is None or (isinstance(email, str) and not email.strip()):
                raise ValidationError("email", "can't be blank")
            other = self._users.find_by_email(email)
            if other and other.id != user_id:
                raise DuplicateEmailError(email)

        if username is not _UNSET:
            if username is None or (isinstance(username, str) and not username.strip()):
                raise ValidationError("username", "can't be blank")
            other = self._users.find_by_username(username)
            if other and other.id != user_id:
                raise DuplicateUsernameError(username)

        new_email = email if email is not _UNSET else user.email
        new_username = username if username is not _UNSET else user.username
        new_password = self._hasher.hash(password) if password else user.hashed_password

        # bio/image: _UNSET means unchanged; None/"" means set to null
        if bio is _UNSET:
            new_bio = user.bio
        elif bio is None or bio == "":
            new_bio = None
        else:
            new_bio = str(bio).strip() or None

        if image is _UNSET:
            new_image = user.image
        elif image is None or image == "":
            new_image = None
        else:
            new_image = str(image).strip() or None

        updated = replace(
            user,
            email=new_email,
            username=new_username,
            hashed_password=new_password,
            bio=new_bio,
            image=new_image,
        )
        saved = self._users.update(updated)
        assert saved.id is not None
        return saved, self._tokens.create(saved.id)
