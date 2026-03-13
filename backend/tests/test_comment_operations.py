"""Behavior: add, list, delete comments."""

import pytest

from app.use_cases.comment_service import CommentService
from app.use_cases.errors import ForbiddenError, NotFoundError
from tests.fakes import FakeArticleRepository, FakeCommentRepository, FakeFollowRepository, FakeUserRepository


def make_service() -> tuple[CommentService, FakeArticleRepository]:
    articles = FakeArticleRepository()
    comments = FakeCommentRepository()
    svc = CommentService(comments, articles)
    return svc, articles


def seed_article(articles: FakeArticleRepository, author_id: int = 1) -> str:
    from app.domain.models import Article
    a = articles.create(Article(slug="my-article", title="My Article", description="d", body="b", author_id=author_id))
    return a.slug


def test_add_comment_returns_comment_with_id():
    svc, articles = make_service()
    seed_article(articles)
    comment = svc.add("my-article", author_id=2, body="Great read!")
    assert comment.id is not None


def test_add_comment_stores_body():
    svc, articles = make_service()
    seed_article(articles)
    comment = svc.add("my-article", author_id=2, body="Great read!")
    assert comment.body == "Great read!"


def test_add_comment_stores_author_id():
    svc, articles = make_service()
    seed_article(articles)
    comment = svc.add("my-article", author_id=42, body="Great read!")
    assert comment.author_id == 42


def test_add_comment_unknown_article_raises():
    svc, _ = make_service()
    with pytest.raises(NotFoundError):
        svc.add("no-such-slug", author_id=1, body="hmm")


def test_list_comments_returns_all_for_article():
    svc, articles = make_service()
    seed_article(articles)
    svc.add("my-article", author_id=1, body="First")
    svc.add("my-article", author_id=2, body="Second")
    comments = svc.list_for_article("my-article")
    assert len(comments) == 2


def test_list_comments_unknown_article_raises():
    svc, _ = make_service()
    with pytest.raises(NotFoundError):
        svc.list_for_article("no-such-slug")


def test_delete_comment_removes_it():
    svc, articles = make_service()
    seed_article(articles)
    comment = svc.add("my-article", author_id=1, body="To delete")
    svc.delete("my-article", comment.id, requester_id=1)
    remaining = svc.list_for_article("my-article")
    assert not any(c.id == comment.id for c in remaining)


def test_delete_comment_by_non_author_raises_forbidden():
    svc, articles = make_service()
    seed_article(articles)
    comment = svc.add("my-article", author_id=1, body="Mine")
    with pytest.raises(ForbiddenError):
        svc.delete("my-article", comment.id, requester_id=99)


def test_delete_comment_unknown_article_raises():
    svc, _ = make_service()
    with pytest.raises(NotFoundError):
        svc.delete("no-such-slug", 1, requester_id=1)


def test_delete_comment_unknown_id_raises():
    svc, articles = make_service()
    seed_article(articles)
    with pytest.raises(NotFoundError):
        svc.delete("my-article", 9999, requester_id=1)
