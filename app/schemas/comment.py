"""Pydantic schemas for comments."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    body: str


class CommentResponse(BaseModel):
    """Schema for comment response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    body: str
    created_at: datetime
    updated_at: datetime
    author: dict  # Will be populated with username, bio, image


class CommentWrapper(BaseModel):
    """Wrapper for single comment response."""
    comment: CommentResponse


class CommentListWrapper(BaseModel):
    """Wrapper for comment list response."""
    comments: list[CommentResponse]
