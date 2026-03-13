from app.domain.models import Comment
from app.ports.interfaces import ArticleRepository, CommentRepository
from app.use_cases.errors import CommentNotFoundError, ForbiddenError, NotFoundError, ValidationError


class CommentService:
    def __init__(
        self,
        comments: CommentRepository,
        articles: ArticleRepository,
    ) -> None:
        self._comments = comments
        self._articles = articles

    def add(self, slug: str, author_id: int, body: str) -> Comment:
        if not body or not body.strip():
            raise ValidationError("body", "can't be blank")
        article = self._articles.find_by_slug(slug)
        if article is None:
            raise NotFoundError(slug)
        assert article.id is not None
        return self._comments.create(Comment(body=body, article_id=article.id, author_id=author_id))

    def list_for_article(self, slug: str) -> list[Comment]:
        article = self._articles.find_by_slug(slug)
        if article is None:
            raise NotFoundError(slug)
        assert article.id is not None
        return self._comments.list_for_article(article.id)

    def delete(self, slug: str, comment_id: int, requester_id: int) -> None:
        article = self._articles.find_by_slug(slug)
        if article is None:
            raise NotFoundError(slug)
        comment = self._comments.find_by_id(comment_id)
        if comment is None:
            raise CommentNotFoundError(str(comment_id))
        if comment.author_id != requester_id:
            raise ForbiddenError()
        self._comments.delete(comment)
