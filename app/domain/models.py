import json
from datetime import datetime
from typing import List, Optional

from sqlmodel import Column, Field, ForeignKey, Integer, Relationship, SQLModel, String


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    password_hash: str = Field()
    bio: Optional[str] = Field(default=None)
    image: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    articles: List["Article"] = Relationship(back_populates="author")
    comments: List["Comment"] = Relationship(back_populates="author")


class Article(SQLModel, table=True):
    __tablename__ = "articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    title: str = Field()
    description: str = Field()
    body: str = Field()
    tag_list_json: str = Field(default="[]")
    favorites_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    author_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id")))

    author: User = Relationship(back_populates="articles")
    comments: List["Comment"] = Relationship(back_populates="article")

    @property
    def tag_list(self) -> List[str]:
        return json.loads(self.tag_list_json) if self.tag_list_json else []

    @tag_list.setter
    def tag_list(self, value: List[str]) -> None:
        self.tag_list_json = json.dumps(value) if value else "[]"


class Comment(SQLModel, table=True):
    __tablename__ = "comments"

    id: Optional[int] = Field(default=None, primary_key=True)
    body: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    author_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id")))
    article_id: int = Field(sa_column=Column(Integer, ForeignKey("articles.id")))

    author: User = Relationship(back_populates="comments")
    article: Article = Relationship(back_populates="comments")


class Favorite(SQLModel, table=True):
    __tablename__ = "favorites"

    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id"), primary_key=True))
    article_id: int = Field(sa_column=Column(Integer, ForeignKey("articles.id"), primary_key=True))


class Follow(SQLModel, table=True):
    __tablename__ = "follows"

    follower_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id"), primary_key=True))
    following_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id"), primary_key=True))
