"""Behavior: article create, read, update, delete."""

import pytest

from app.use_cases.article_service import ArticleService
from app.use_cases.errors import ForbiddenError, NotFoundError, ValidationError
from tests.fakes import FakeArticleRepository, FakeFollowRepository, FakeUserRepository


def make_service() -> ArticleService:
    return ArticleService(FakeArticleRepository(), FakeUserRepository(), FakeFollowRepository())


def test_create_article_returns_slug():
    svc = make_service()
    article = svc.create(1, "How to Train a Dragon", "desc", "body")
    assert article.slug == "how-to-train-a-dragon"


def test_create_article_stores_title():
    svc = make_service()
    article = svc.create(1, "My Title", "desc", "body")
    assert article.title == "My Title"


def test_create_article_stores_description():
    svc = make_service()
    article = svc.create(1, "My Title", "My description", "body")
    assert article.description == "My description"


def test_create_article_stores_body():
    svc = make_service()
    article = svc.create(1, "My Title", "desc", "The body text")
    assert article.body == "The body text"


def test_create_article_stores_author_id():
    svc = make_service()
    article = svc.create(42, "My Title", "desc", "body")
    assert article.author_id == 42


def test_create_article_with_tags():
    svc = make_service()
    article = svc.create(1, "My Title", "desc", "body", ["python", "fastapi"])
    assert "python" in article.tag_list
    assert "fastapi" in article.tag_list


def test_create_article_without_tags_has_empty_list():
    svc = make_service()
    article = svc.create(1, "My Title", "desc", "body")
    assert article.tag_list == []


def test_create_article_slug_collision_appends_suffix():
    svc = make_service()
    a1 = svc.create(1, "Same Title", "desc", "body")
    a2 = svc.create(1, "Same Title", "desc", "body")
    assert a1.slug != a2.slug
    assert a2.slug.startswith("same-title-")


def test_create_article_blank_title_raises():
    svc = make_service()
    with pytest.raises(ValidationError) as exc_info:
        svc.create(1, "", "desc", "body")
    assert exc_info.value.field == "title"


def test_get_article_by_slug():
    svc = make_service()
    svc.create(1, "My Title", "desc", "body")
    article = svc.get("my-title")
    assert article.slug == "my-title"


def test_get_article_not_found_raises():
    svc = make_service()
    with pytest.raises(NotFoundError):
        svc.get("nonexistent-slug")


def test_update_article_title_changes_slug():
    svc = make_service()
    svc.create(1, "Original Title", "desc", "body")
    updated = svc.update("original-title", 1, title="New Title")
    assert updated.slug == "new-title"
    assert updated.title == "New Title"


def test_update_article_by_non_owner_raises_forbidden():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    with pytest.raises(ForbiddenError):
        svc.update("my-article", requester_id=99, title="Hacked")


def test_update_article_not_found_raises():
    svc = make_service()
    with pytest.raises(NotFoundError):
        svc.update("no-such-slug", 1, title="New")


def test_delete_article_removes_it():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    svc.delete("my-article", 1)
    with pytest.raises(NotFoundError):
        svc.get("my-article")


def test_delete_article_by_non_owner_raises_forbidden():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    with pytest.raises(ForbiddenError):
        svc.delete("my-article", requester_id=99)


def test_delete_article_not_found_raises():
    svc = make_service()
    with pytest.raises(NotFoundError):
        svc.delete("no-such-slug", 1)


def test_all_tags_returns_distinct_tags():
    svc = make_service()
    svc.create(1, "Article One", "desc", "body", ["python", "fastapi"])
    svc.create(1, "Article Two", "desc", "body", ["python", "sqlmodel"])
    tags = svc.all_tags()
    assert sorted(tags) == ["fastapi", "python", "sqlmodel"]


def test_favorite_increments_favorites_count():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    article = svc.favorite("my-article", user_id=2)
    assert article.favorites_count == 1


def test_unfavorite_decrements_favorites_count():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    svc.favorite("my-article", user_id=2)
    article = svc.unfavorite("my-article", user_id=2)
    assert article.favorites_count == 0


def test_favorite_is_idempotent():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    svc.favorite("my-article", user_id=2)
    article = svc.favorite("my-article", user_id=2)
    assert article.favorites_count == 1


def test_unfavorite_is_idempotent():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    article = svc.unfavorite("my-article", user_id=2)
    assert article.favorites_count == 0


def test_is_favorited_true_after_favorite():
    svc = make_service()
    article = svc.create(1, "My Article", "desc", "body")
    svc.favorite("my-article", user_id=2)
    article = svc.get("my-article")
    assert svc.is_favorited(article, user_id=2) is True


def test_is_favorited_false_for_other_user():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    svc.favorite("my-article", user_id=2)
    article = svc.get("my-article")
    assert svc.is_favorited(article, user_id=3) is False


def test_is_favorited_false_when_no_viewer():
    svc = make_service()
    svc.create(1, "My Article", "desc", "body")
    article = svc.get("my-article")
    assert svc.is_favorited(article, user_id=None) is False
