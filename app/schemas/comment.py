"""Pydantic schemas for comments."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    body: str


class CommentAuthorProfile(BaseModel):
    """Author info in comment response."""
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool = False


class CommentResponse(BaseModel):
    """Schema for comment response (camelCase)."""
    id: int
    body: str
    createdAt: datetime
    updatedAt: datetime
    author: CommentAuthorProfile


class CommentWrapper(BaseModel):
    """Wrapper for single comment response."""
    comment: CommentResponse


class CommentListWrapper(BaseModel):
    """Wrapper for comment list response."""
    comments: List[CommentResponse]
