from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AuthorProfile(BaseModel):
    username: str
    bio: Optional[str] = None
    image: Optional[str] = None
    following: bool = False


class ArticleCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    tag_list: Optional[List[str]] = Field(default_factory=list, alias="tagList")

    @field_validator("title", "description", "body", mode="before")
    @classmethod
    def not_blank(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError("can't be blank")
        return v


class ArticleUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = Field(default=None, min_length=1)
    body: Optional[str] = Field(default=None, min_length=1)
    tag_list: Optional[List[str]] = Field(default=None, alias="tagList")

    @field_validator("tag_list", mode="before")
    @classmethod
    def tag_list_not_null(cls, v):
        if v is None:
            raise ValueError("can't be null")
        return v


class ArticleResponse(BaseModel):
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
    article: ArticleResponse


class ArticleListWrapper(BaseModel):
    articles: List[ArticleListItem]
    articlesCount: int


class TagListWrapper(BaseModel):
    tags: List[str]
