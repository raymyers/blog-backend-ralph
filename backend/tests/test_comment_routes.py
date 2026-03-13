"""Route behavior: comment endpoints."""

from fastapi.testclient import TestClient


def _register(client: TestClient, username="alice", email="alice@example.com"):
    resp = client.post(
        "/api/users",
        json={"user": {"username": username, "email": email, "password": "s3cret"}},
    )
    return resp.json()["user"]["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


def _create_article(client, token, title="Hello"):
    resp = client.post(
        "/api/articles",
        json={"article": {"title": title, "description": "d", "body": "b"}},
        headers=_auth(token),
    )
    return resp.json()["article"]["slug"]


def _add_comment(client, token, slug, body="Great read!"):
    return client.post(
        f"/api/articles/{slug}/comments",
        json={"comment": {"body": body}},
        headers=_auth(token),
    )


# ── Add Comment ────────────────────────────────────────────────────────────────


def test_add_comment_returns_201(client):
    token = _register(client)
    slug = _create_article(client, token)
    resp = _add_comment(client, token, slug)
    assert resp.status_code == 201


def test_add_comment_returns_comment_data(client):
    token = _register(client)
    slug = _create_article(client, token)
    resp = _add_comment(client, token, slug, body="Nice!")
    data = resp.json()["comment"]
    assert data["body"] == "Nice!"
    assert data["id"] is not None
    assert data["author"]["username"] == "alice"


def test_add_comment_blank_body_returns_422(client):
    token = _register(client)
    slug = _create_article(client, token)
    resp = _add_comment(client, token, slug, body="")
    assert resp.status_code == 422
    assert resp.json()["errors"]["body"][0] == "can't be blank"


def test_add_comment_unknown_article_returns_404(client):
    token = _register(client)
    resp = _add_comment(client, token, "no-such-slug")
    assert resp.status_code == 404
    assert resp.json()["errors"]["article"][0] == "not found"


def test_add_comment_without_auth_returns_401(client):
    token = _register(client)
    slug = _create_article(client, token)
    resp = client.post(
        f"/api/articles/{slug}/comments",
        json={"comment": {"body": "Hi"}},
    )
    assert resp.status_code == 401


# ── List Comments ──────────────────────────────────────────────────────────────


def test_list_comments_returns_list(client):
    token = _register(client)
    slug = _create_article(client, token)
    _add_comment(client, token, slug, "First")
    _add_comment(client, token, slug, "Second")
    resp = client.get(f"/api/articles/{slug}/comments")
    assert resp.status_code == 200
    assert len(resp.json()["comments"]) == 2


def test_list_comments_unknown_article_returns_404(client):
    resp = client.get("/api/articles/no-such/comments")
    assert resp.status_code == 404
    assert resp.json()["errors"]["article"][0] == "not found"


# ── Delete Comment ─────────────────────────────────────────────────────────────


def test_delete_comment_returns_204(client):
    token = _register(client)
    slug = _create_article(client, token)
    comment_resp = _add_comment(client, token, slug)
    comment_id = comment_resp.json()["comment"]["id"]
    resp = client.delete(f"/api/articles/{slug}/comments/{comment_id}", headers=_auth(token))
    assert resp.status_code == 204


def test_delete_comment_by_non_owner_returns_403(client):
    alice_token = _register(client, username="alice", email="alice@example.com")
    bob_token = _register(client, username="bob", email="bob@example.com")
    slug = _create_article(client, alice_token)
    comment_resp = _add_comment(client, alice_token, slug)
    comment_id = comment_resp.json()["comment"]["id"]
    resp = client.delete(f"/api/articles/{slug}/comments/{comment_id}", headers=_auth(bob_token))
    assert resp.status_code == 403
    assert resp.json()["errors"]["comment"][0] == "forbidden"


def test_delete_nonexistent_comment_returns_404(client):
    token = _register(client)
    slug = _create_article(client, token)
    resp = client.delete(f"/api/articles/{slug}/comments/99999", headers=_auth(token))
    assert resp.status_code == 404
    assert resp.json()["errors"]["comment"][0] == "not found"
