from typing import Optional

from pydantic import BaseModel, field_validator


class UserCreate(BaseModel):
    email: str
    username: str
    password: str

    @field_validator("email", "username", "password", mode="before")
    @classmethod
    def not_blank(cls, v):
        if v is None or str(v).strip() == "":
            raise ValueError("can't be blank")
        return v


class UserLogin(BaseModel):
    email: str
    password: str

    @field_validator("email", "password", mode="before")
    @classmethod
    def not_blank(cls, v):
        if v is None or str(v).strip() == "":
            raise ValueError("can't be blank")
        return v


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[str] = None

    @field_validator("email", "username", mode="before")
    @classmethod
    def no_blank_required(cls, v):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            raise ValueError("can't be blank")
        return v


class UserWithToken(BaseModel):
    email: str
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    token: str


class UserWithTokenWrapper(BaseModel):
    user: UserWithToken


class LoginRequest(BaseModel):
    user: UserLogin


class RegisterRequest(BaseModel):
    user: UserCreate
