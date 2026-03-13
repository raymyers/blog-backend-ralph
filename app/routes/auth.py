from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import ValidationError as PydanticValidationError
from sqlmodel import Session

from app.adapters.database import SQLModelUserRepository
from app.adapters.password import PasslibPasswordHasher
from app.adapters.token import JWTTokenGenerator, _SECRET_KEY, _ALGORITHM
from app.database import get_session
from app.domain.models import User
from app.schemas.user import (
    LoginRequest,
    RegisterRequest,
    UserUpdate,
    UserWithToken,
    UserWithTokenWrapper,
)
from app.use_cases.user_service import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    UserService,
)

router = APIRouter(prefix="/api", tags=["auth"])


def _extract_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    for prefix in ("Token ", "Bearer "):
        if auth.startswith(prefix):
            return auth[len(prefix):]
    return None


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(
        SQLModelUserRepository(session),
        PasslibPasswordHasher(),
        JWTTokenGenerator(),
    )


async def get_current_user_optional(
    request: Request,
    session: Session = Depends(get_session),
) -> Optional[User]:
    token = _extract_token(request)
    if not token:
        return None
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    return await SQLModelUserRepository(session).get_by_id(int(user_id))


async def get_current_user_required(
    request: Request,
    session: Session = Depends(get_session),
) -> User:
    token = _extract_token(request)
    if not token:
        raise HTTPException(status_code=401, detail={"errors": {"token": ["is missing"]}})
    try:
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail={"errors": {"token": ["is missing"]}})
    except JWTError:
        raise HTTPException(status_code=401, detail={"errors": {"token": ["is missing"]}})
    user = await SQLModelUserRepository(session).get_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=401, detail={"errors": {"token": ["is missing"]}})
    return user


def _wrap(user: User, token: str) -> UserWithTokenWrapper:
    return UserWithTokenWrapper(
        user=UserWithToken(email=user.email, username=user.username, bio=user.bio, image=user.image, token=token)
    )


@router.post("/users", response_model=UserWithTokenWrapper, status_code=201)
async def register(body: RegisterRequest, svc: UserService = Depends(get_user_service)):
    try:
        user, token = await svc.register(body.user)
    except DuplicateEmailError:
        raise HTTPException(409, detail={"errors": {"email": ["has already been taken"]}})
    except DuplicateUsernameError:
        raise HTTPException(409, detail={"errors": {"username": ["has already been taken"]}})
    return _wrap(user, token)


@router.post("/users/login", response_model=UserWithTokenWrapper)
async def login(body: LoginRequest, svc: UserService = Depends(get_user_service)):
    try:
        user, token = await svc.login(body.user.email, body.user.password)
    except InvalidCredentialsError:
        raise HTTPException(401, detail={"errors": {"credentials": ["invalid"]}})
    return _wrap(user, token)


@router.get("/user", response_model=UserWithTokenWrapper)
async def get_current_user_endpoint(
    current_user: User = Depends(get_current_user_required),
    svc: UserService = Depends(get_user_service),
):
    token = await svc.generate_fresh_token(current_user)
    return _wrap(current_user, token)


@router.put("/user", response_model=UserWithTokenWrapper)
async def update_current_user(
    body: dict = Body(...),
    current_user: User = Depends(get_current_user_required),
    svc: UserService = Depends(get_user_service),
):
    try:
        user_update = UserUpdate(**body.get("user", {}))
    except PydanticValidationError as exc:
        errors: dict = {}
        for error in exc.errors():
            loc = error.get("loc", [])
            field = str(loc[-1]) if loc else "body"
            msg = error.get("msg", "is invalid")
            if msg.startswith("Value error, "):
                msg = msg[len("Value error, "):]
            errors.setdefault(field, []).append(msg)
        raise HTTPException(422, detail={"errors": errors})

    try:
        updated = await svc.update_user(current_user.id, user_update)
    except DuplicateEmailError:
        raise HTTPException(409, detail={"errors": {"email": ["has already been taken"]}})
    except DuplicateUsernameError:
        raise HTTPException(409, detail={"errors": {"username": ["has already been taken"]}})

    token = await svc.generate_fresh_token(updated)
    return _wrap(updated, token)
