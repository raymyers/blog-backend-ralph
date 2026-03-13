"""Domain models for the blog backend."""
from datetime import datetime
from typing import Optional, List

from sqlmodel import Field, SQLModel, Column, Integer, String, ForeignKey, Relationship


class User(SQLModel, table=True):
    """User entity for authentication and profile."""
    
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str = Field(unique=True, index=True)
    password_hash: str = Field()
    bio: Optional[str] = Field(default=None)
    image: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    articles: List["Article"] = Relationship(back_populates="author")
    comments: List["Comment"] = Relationship(back_populates="author")


class Article(SQLModel, table=True):
    """Article entity."""
    
    __tablename__ = "articles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    title: str = Field()
    description: str = Field()
    body: str = Field()
    # Store tags as JSON string for SQLite compatibility
    tag_list_json: str = Field(default="[]")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign keys
    author_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id")))
    
    # Relationships
    author: User = Relationship(back_populates="articles")
    comments: List["Comment"] = Relationship(back_populates="article")
    
    # Favorites count
    favorites_count: int = Field(default=0)
    
    @property
    def tag_list(self) -> List[str]:
        """Get tag list from JSON."""
        import json
        return json.loads(self.tag_list_json) if self.tag_list_json else []
    
    @tag_list.setter
    def tag_list(self, value: List[str]):
        """Set tag list as JSON."""
        import json
        self.tag_list_json = json.dumps(value) if value else "[]"


class Comment(SQLModel, table=True):
    """Comment entity."""
    
    __tablename__ = "comments"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    body: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Foreign keys
    author_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id")))
    article_id: int = Field(sa_column=Column(Integer, ForeignKey("articles.id")))
    
    # Relationships
    author: User = Relationship(back_populates="comments")
    article: Article = Relationship(back_populates="comments")


# Association table for favorites (many-to-many)
class Favorite(SQLModel, table=True):
    """User-Article favorite relationship."""
    
    __tablename__ = "favorites"
    
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id"), primary_key=True))
    article_id: int = Field(sa_column=Column(Integer, ForeignKey("articles.id"), primary_key=True))


# Association table for follows (many-to-many)
class Follow(SQLModel, table=True):
    """User-User follow relationship."""
    
    __tablename__ = "follows"
    
    follower_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id"), primary_key=True))
    following_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id"), primary_key=True))
