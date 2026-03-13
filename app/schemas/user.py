"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: str
    username: str
    password: str

    @field_validator("email", "username", "password", mode="before")
    @classmethod
    def not_blank(cls, v, info):
        if v is None or str(v).strip() == "":
            raise ValueError("can't be blank")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: str
    password: str

    @field_validator("email", "password", mode="before")
    @classmethod
    def not_blank(cls, v, info):
        if v is None or str(v).strip() == "":
            raise ValueError("can't be blank")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    bio: Optional[str] = None
    image: Optional[str] = None

    @field_validator("email", "username", mode="before")
    @classmethod
    def no_blank_required(cls, v, info):
        if v is None or (isinstance(v, str) and v.strip() == ""):
            raise ValueError("can't be blank")
        return v


class UserWithToken(BaseModel):
    """Schema for user with JWT token."""
    email: str
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    token: str


class UserWithTokenWrapper(BaseModel):
    """Wrapper for user with token in API response."""
    user: UserWithToken


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    errors: dict = Field(default_factory=dict)


class LoginRequest(BaseModel):
    """Wrapper for login request."""
    user: UserLogin


class RegisterRequest(BaseModel):
    """Wrapper for registration request."""
    user: UserCreate


# Keep for backward compat
UserResponse = UserWithToken
UserResponseWrapper = UserWithTokenWrapper
