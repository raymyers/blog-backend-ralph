from typing import List

from sqlmodel import Session, select

from app.domain.models import Article, Comment, User


class CommentService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _get_article(self, slug: str) -> Article:
        article = self.session.exec(select(Article).where(Article.slug == slug)).first()
        if not article:
            raise KeyError("article")
        return article

    async def create_comment(self, article_slug: str, author: User, body: str) -> Comment:
        article = self._get_article(article_slug)
        comment = Comment(body=body, author_id=author.id, article_id=article.id)
        self.session.add(comment)
        self.session.commit()
        self.session.refresh(comment)
        return comment

    async def get_comments(self, article_slug: str) -> List[Comment]:
        article = self._get_article(article_slug)
        stmt = select(Comment).where(Comment.article_id == article.id).order_by(Comment.created_at.desc())
        return list(self.session.exec(stmt).all())

    async def delete_comment(self, article_slug: str, comment_id: int, user_id: int) -> None:
        article = self._get_article(article_slug)
        stmt = select(Comment).where(Comment.id == comment_id, Comment.article_id == article.id)
        comment = self.session.exec(stmt).first()
        if not comment:
            raise KeyError("comment")
        if comment.author_id != user_id:
            raise PermissionError("forbidden")
        self.session.delete(comment)
        self.session.commit()
