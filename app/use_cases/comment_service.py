"""Comment service for comment operations."""
from datetime import datetime
from typing import Optional, List
from sqlmodel import select

from app.domain.models import Comment, Article, User
from app.adapters.database import SQLModelUserRepository


class CommentService:
    """Service for comment operations."""
    
    def __init__(self, session):
        self.session = session
    
    async def create_comment(self, article_slug: str, author: User, body: str) -> Optional[Comment]:
        """Create a new comment on an article."""
        # Get article
        statement = select(Article).where(Article.slug == article_slug)
        article = self.session.exec(statement).first()
        
        if not article:
            return None
        
        # Create comment
        comment = Comment(
            body=body,
            author_id=author.id,
            article_id=article.id,
        )
        
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(comment)
        
        return comment
    
    async def get_comments(self, article_slug: str) -> List[Comment]:
        """Get all comments for an article."""
        # Get article
        statement = select(Article).where(Article.slug == article_slug)
        article = self.session.exec(statement).first()
        
        if not article:
            return []
        
        # Get comments
        statement = select(Comment).where(Comment.article_id == article.id).order_by(Comment.created_at.desc())
        return list(self.session.exec(statement).all())
    
    async def delete_comment(self, article_slug: str, comment_id: int, user_id: int) -> bool:
        """Delete a comment."""
        # Get article
        statement = select(Article).where(Article.slug == article_slug)
        article = self.session.exec(statement).first()
        
        if not article:
            return False
        
        # Get comment
        statement = select(Comment).where(Comment.id == comment_id, Comment.article_id == article.id)
        comment = self.session.exec(statement).first()
        
        if not comment:
            return False
        
        # Check ownership
        if comment.author_id != user_id:
            return False
        
        self.session.delete(comment)
        self.session.commit()
        
        return True
