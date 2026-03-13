"""Pydantic schemas for articles."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


class AuthorProfile(BaseModel):
    """Author info embedded in article response."""
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool = False


class ArticleCreate(BaseModel):
    """Schema for creating an article."""
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    tag_list: Optional[List[str]] = Field(default_factory=list, alias='tagList')

    @field_validator('title', 'description', 'body', mode='before')
    @classmethod
    def not_blank(cls, v, info):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("can't be blank")
        return v


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = Field(default=None, min_length=1)
    body: Optional[str] = Field(default=None, min_length=1)
    tag_list: Optional[List[str]] = Field(default=None, alias='tagList')

    @field_validator('tag_list', mode='before')
    @classmethod
    def tag_list_not_null(cls, v, info):
        if v is None:
            raise ValueError("can't be null")
        return v


class ArticleResponse(BaseModel):
    """Single article response (includes body)."""
    slug: str
    title: str
    description: str
    body: str
    tagList: List[str] = Field(default_factory=list)
    createdAt: datetime
    updatedAt: datetime
    favorited: bool = False
    favoritesCount: int = 0
    author: AuthorProfile


class ArticleListItem(BaseModel):
    """Article in list response (no body field)."""
    slug: str
    title: str
    description: str
    tagList: List[str] = Field(default_factory=list)
    createdAt: datetime
    updatedAt: datetime
    favorited: bool = False
    favoritesCount: int = 0
    author: AuthorProfile


class ArticleWrapper(BaseModel):
    """Wrapper for single article response."""
    article: ArticleResponse


class ArticleListWrapper(BaseModel):
    """Wrapper for article list response."""
    articles: List[ArticleListItem]
    articlesCount: int


class TagListWrapper(BaseModel):
    """Wrapper for tag list response."""
    tags: List[str]


# Keep for backward compat
ArticleListResponse = ArticleListItem
