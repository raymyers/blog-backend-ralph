"""Authentication routes and dependency."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import ValidationError

from app.database import get_session
from app.adapters.database import SQLModelUserRepository
from app.adapters.password import PasslibPasswordHasher
from app.adapters.token import JWTTokenGenerator
from app.use_cases.user_service import UserService
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

# Security
security = HTTPBearer()


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    """Dependency to get UserService with injected adapters."""
    user_repo = SQLModelUserRepository(session)
    password_hasher = PasslibPasswordHasher()
    token_generator = JWTTokenGenerator()
    return UserService(user_repo, password_hasher, token_generator)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token = credentials.credentials
    
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
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": {"body": [str(e)]}},
        )


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
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"errors": {"body": ["Invalid credentials"]}},
        )


@router.get("/user", response_model=UserWithTokenWrapper)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Get current user."""
    # Generate fresh token
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
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Update current user."""
    user_data = body.get("user", {})
    user_update = UserUpdate(**user_data)
    
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
