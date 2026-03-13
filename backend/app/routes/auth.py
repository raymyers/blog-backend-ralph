from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.deps import RequiredUserIdDep, UserServiceDep
from app.domain.models import User
from app.use_cases.errors import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    ValidationError,
)

router = APIRouter()


def _user_response(user: User, token: str) -> dict[str, Any]:
    return {
        "user": {
            "email": user.email,
            "token": token,
            "username": user.username,
            "bio": user.bio,
            "image": user.image,
        }
    }


class RegisterInput(BaseModel):
    user: dict[str, Any]


class LoginInput(BaseModel):
    user: dict[str, Any]


class UpdateUserInput(BaseModel):
    user: dict[str, Any]


@router.post("/users", status_code=201)
def register(body: RegisterInput, svc: UserServiceDep):
    data = body.user
    try:
        user, token = svc.register(
            username=data.get("username", ""),
            email=data.get("email", ""),
            password=data.get("password", ""),
        )
    except ValidationError as e:
        raise HTTPException(422, detail={"errors": {e.field: [e.message]}})
    except DuplicateEmailError:
        raise HTTPException(409, detail={"errors": {"email": ["has already been taken"]}})
    except DuplicateUsernameError:
        raise HTTPException(409, detail={"errors": {"username": ["has already been taken"]}})
    return _user_response(user, token)


@router.post("/users/login")
def login(body: LoginInput, svc: UserServiceDep):
    data = body.user
    try:
        user, token = svc.login(
            email=data.get("email", ""),
            password=data.get("password", ""),
        )
    except ValidationError as e:
        raise HTTPException(422, detail={"errors": {e.field: [e.message]}})
    except InvalidCredentialsError:
        raise HTTPException(401, detail={"errors": {"credentials": ["invalid"]}})
    return _user_response(user, token)


@router.get("/user")
def get_current_user(user_id: RequiredUserIdDep, svc: UserServiceDep):
    try:
        user, token = svc.get_current_user(user_id)
    except InvalidCredentialsError:
        raise HTTPException(401, detail={"errors": {"token": ["is invalid"]}})
    return _user_response(user, token)


@router.put("/user")
def update_user(body: UpdateUserInput, user_id: RequiredUserIdDep, svc: UserServiceDep):
    data = body.user
    kwargs: dict[str, Any] = {}
    if "email" in data:
        kwargs["email"] = data["email"]
    if "username" in data:
        kwargs["username"] = data["username"]
    if "password" in data:
        kwargs["password"] = data["password"]
    if "bio" in data:
        kwargs["bio"] = data["bio"]
    if "image" in data:
        kwargs["image"] = data["image"]

    try:
        user, token = svc.update_user(user_id, **kwargs)
    except ValidationError as e:
        raise HTTPException(422, detail={"errors": {e.field: [e.message]}})
    except DuplicateEmailError:
        raise HTTPException(409, detail={"errors": {"email": ["has already been taken"]}})
    except DuplicateUsernameError:
        raise HTTPException(409, detail={"errors": {"username": ["has already been taken"]}})
    except InvalidCredentialsError:
        raise HTTPException(401, detail={"errors": {"token": ["is invalid"]}})
    return _user_response(user, token)
