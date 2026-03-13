"""Authentication routes and dependency."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Body
from sqlmodel import Session
from jose import JWTError, jwt

from app.database import get_session
from app.adapters.database import SQLModelUserRepository
from app.adapters.password import PasslibPasswordHasher
from app.adapters.token import JWTTokenGenerator
from app.use_cases.user_service import UserService, DuplicateEmailError, DuplicateUsernameError, InvalidCredentialsError
from pydantic import ValidationError as PydanticValidationError
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponseWrapper,
    UserWithTokenWrapper,
    UserWithToken,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.domain.models import User


# JWT settings (should match adapter)
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

# Router
router = APIRouter(prefix="/api", tags=["auth"])


def _extract_token(request: Request) -> Optional[str]:
    """Extract JWT from 'Authorization: Token <jwt>' or 'Authorization: Bearer <jwt>'."""
    auth = request.headers.get("Authorization", "")
    for prefix in ("Token ", "Bearer "):
        if auth.startswith(prefix):
            return auth[len(prefix):]
    return None


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    """Dependency to get UserService with injected adapters."""
    user_repo = SQLModelUserRepository(session)
    password_hasher = PasslibPasswordHasher()
    token_generator = JWTTokenGenerator()
    return UserService(user_repo, password_hasher, token_generator)


async def get_current_user_optional(
    request: Request,
    session: Session = Depends(get_session),
) -> Optional[User]:
    """Get current authenticated user from JWT token (optional)."""
    token = _extract_token(request)
    if token is None:
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user_repo = SQLModelUserRepository(session)
    return await user_repo.get_by_id(int(user_id))


# Alias for backward compatibility
get_current_user = get_current_user_optional


async def get_current_user_required(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token (required)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"errors": {"token": ["is missing"]}},
    )

    token = _extract_token(request)
    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_repo = SQLModelUserRepository(session)
    user = await user_repo.get_by_id(int(user_id))

    if user is None:
        raise credentials_exception

    return user


@router.post(
    "/users",
    response_model=UserWithTokenWrapper,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    user_service: UserService = Depends(get_user_service),
):
    """Register a new user."""
    try:
        user, token = await user_service.register(request.user)
        return UserWithTokenWrapper(
            user=UserWithToken(
                email=user.email,
                username=user.username,
                bio=user.bio,
                image=user.image,
                token=token,
            )
        )
    except DuplicateEmailError:
        raise HTTPException(status_code=409, detail={"errors": {"email": ["has already been taken"]}})
    except DuplicateUsernameError:
        raise HTTPException(status_code=409, detail={"errors": {"username": ["has already been taken"]}})


@router.post("/users/login", response_model=UserWithTokenWrapper)
async def login(
    request: LoginRequest,
    user_service: UserService = Depends(get_user_service),
):
    """Login user."""
    try:
        user, token = await user_service.login(request.user.email, request.user.password)
        return UserWithTokenWrapper(
            user=UserWithToken(
                email=user.email,
                username=user.username,
                bio=user.bio,
                image=user.image,
                token=token,
            )
        )
    except InvalidCredentialsError:
        raise HTTPException(status_code=401, detail={"errors": {"credentials": ["invalid"]}})


@router.get("/user", response_model=UserWithTokenWrapper)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user_required),
    user_service: UserService = Depends(get_user_service),
):
    """Get current user."""
    token = await user_service.generate_fresh_token(current_user)

    return UserWithTokenWrapper(
        user=UserWithToken(
            email=current_user.email,
            username=current_user.username,
            bio=current_user.bio,
            image=current_user.image,
            token=token,
        )
    )


@router.put("/user", response_model=UserWithTokenWrapper)
async def update_current_user(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    user_service: UserService = Depends(get_user_service),
):
    """Update current user."""
    user_data = body.get("user", {})
    try:
        user_update = UserUpdate(**user_data)
    except PydanticValidationError as exc:
        errors = {}
        for error in exc.errors():
            loc = error.get("loc", [])
            field = str(loc[-1]) if loc else "body"
            msg_raw = error.get("msg", "is invalid")
            msg = msg_raw[len("Value error, "):] if msg_raw.startswith("Value error, ") else msg_raw
            if field not in errors:
                errors[field] = []
            errors[field].append(msg)
        raise HTTPException(status_code=422, detail={"errors": errors})

    try:
        updated_user = await user_service.update_user(current_user.id, user_update)
        token = await user_service.generate_fresh_token(updated_user)
        return UserWithTokenWrapper(
            user=UserWithToken(
                email=updated_user.email,
                username=updated_user.username,
                bio=updated_user.bio,
                image=updated_user.image,
                token=token,
            )
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": {"body": [str(e)]}},
        )
