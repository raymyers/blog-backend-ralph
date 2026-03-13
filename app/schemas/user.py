"""Pydantic schemas for API request/response validation."""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Request Schemas


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    model_config = ConfigDict(validate_default=True)
    
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    password: Optional[str] = Field(default=None, min_length=8)
    bio: Optional[str] = None
    image: Optional[str] = None


# Response Schemas


class UserResponse(BaseModel):
    """Schema for user in responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserWithToken(BaseModel):
    """Schema for user with JWT token."""
    email: str
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    token: str


class UserResponseWrapper(BaseModel):
    """Wrapper for user in API response."""
    user: UserResponse


class UserWithTokenWrapper(BaseModel):
    """Wrapper for user with token in API response."""
    user: UserWithToken


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    errors: dict = Field(default_factory=dict)


# Auth


class LoginRequest(BaseModel):
    """Wrapper for login request."""
    user: UserLogin


class RegisterRequest(BaseModel):
    """Wrapper for registration request."""
    user: UserCreate
