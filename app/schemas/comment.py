from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CommentCreate(BaseModel):
    body: str


class CommentAuthorProfile(BaseModel):
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool = False


class CommentResponse(BaseModel):
    id: int
    body: str
    createdAt: datetime
    updatedAt: datetime
    author: CommentAuthorProfile


class CommentWrapper(BaseModel):
    comment: CommentResponse


class CommentListWrapper(BaseModel):
    comments: List[CommentResponse]
