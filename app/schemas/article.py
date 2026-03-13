"""Pydantic schemas for articles."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AuthorResponse(BaseModel):
    """Author info embedded in article response."""
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None


class ArticleCreate(BaseModel):
    """Schema for creating an article."""
    model_config = ConfigDict(populate_by_name=True)
    
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    tag_list: Optional[List[str]] = Field(default_factory=list, validation_alias='tagList')


class ArticleUpdate(BaseModel):
    """Schema for updating an article."""
    model_config = ConfigDict(populate_by_name=True)
    
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = Field(default=None, min_length=1)
    body: Optional[str] = Field(default=None, min_length=1)
    tag_list: Optional[List[str]] = Field(default=None, validation_alias='tagList')


class ArticleResponse(BaseModel):
    """Schema for article response."""
    model_config = ConfigDict(from_attributes=True)
    
    slug: str
    title: str
    description: str
    body: str
    tag_list: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    favorited: bool = False
    favorites_count: int = 0
    author: AuthorResponse


class ArticleListResponse(BaseModel):
    """Schema for article list response (without body)."""
    model_config = ConfigDict(from_attributes=True)
    
    slug: str
    title: str
    description: str
    tag_list: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    favorited: bool = False
    favorites_count: int = 0
    author: AuthorResponse


class ArticleWrapper(BaseModel):
    """Wrapper for single article response."""
    article: ArticleResponse


class ArticleListWrapper(BaseModel):
    """Wrapper for article list response."""
    articles: List[ArticleListResponse]
    articles_count: int


class TagListWrapper(BaseModel):
    """Wrapper for tag list response."""
    tags: List[str]
