"""Route behavior: article endpoints."""

from fastapi.testclient import TestClient


def _register(client: TestClient, username="alice", email="alice@example.com"):
    resp = client.post(
        "/api/users",
        json={"user": {"username": username, "email": email, "password": "s3cret"}},
    )
    return resp.json()["user"]["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


def _create_article(client, token, title="Hello World", description="desc", body="content", tag_list=None):
    payload: dict = {"title": title, "description": description, "body": body}
    if tag_list is not None:
        payload["tagList"] = tag_list
    return client.post("/api/articles", json={"article": payload}, headers=_auth(token))


# ── Create ────────────────────────────────────────────────────────────────────


def test_create_article_returns_201(client):
    token = _register(client)
    resp = _create_article(client, token)
    assert resp.status_code == 201


def test_create_article_returns_article_data(client):
    token = _register(client)
    resp = _create_article(client, token, title="My Title")
    data = resp.json()["article"]
    assert data["title"] == "My Title"
    assert data["slug"] == "my-title"
    assert data["description"] == "desc"
    assert data["body"] == "content"


def test_create_article_with_tags(client):
    token = _register(client)
    resp = _create_article(client, token, tag_list=["python", "fastapi"])
    assert set(resp.json()["article"]["tagList"]) == {"python", "fastapi"}


def test_create_article_blank_title_returns_422(client):
    token = _register(client)
    resp = _create_article(client, token, title="")
    assert resp.status_code == 422
    assert resp.json()["errors"]["title"][0] == "can't be blank"


def test_create_article_blank_description_returns_422(client):
    token = _register(client)
    resp = _create_article(client, token, description="")
    assert resp.status_code == 422
    assert resp.json()["errors"]["description"][0] == "can't be blank"


def test_create_article_blank_body_returns_422(client):
    token = _register(client)
    resp = _create_article(client, token, body="")
    assert resp.status_code == 422
    assert resp.json()["errors"]["body"][0] == "can't be blank"


def test_create_article_without_auth_returns_401(client):
    resp = client.post("/api/articles", json={"article": {"title": "T", "description": "D", "body": "B"}})
    assert resp.status_code == 401


# ── Read ──────────────────────────────────────────────────────────────────────


def test_get_article_by_slug(client):
    token = _register(client)
    _create_article(client, token, title="Read Me")
    resp = client.get("/api/articles/read-me")
    assert resp.status_code == 200
    assert resp.json()["article"]["slug"] == "read-me"


def test_get_article_unknown_slug_returns_404(client):
    resp = client.get("/api/articles/no-such-article")
    assert resp.status_code == 404
    assert resp.json()["errors"]["article"][0] == "not found"


# ── Update ────────────────────────────────────────────────────────────────────


def test_update_article_title_changes_slug(client):
    token = _register(client)
    _create_article(client, token, title="Original")
    resp = client.put(
        "/api/articles/original",
        json={"article": {"title": "Updated"}},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["article"]["slug"] == "updated"


def test_update_article_tag_list_replaces_tags(client):
    token = _register(client)
    _create_article(client, token, title="Tagged", tag_list=["old"])
    resp = client.put(
        "/api/articles/tagged",
        json={"article": {"tagList": ["new1", "new2"]}},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert set(resp.json()["article"]["tagList"]) == {"new1", "new2"}


def test_update_article_empty_tag_list_removes_tags(client):
    token = _register(client)
    _create_article(client, token, title="Has Tags", tag_list=["a", "b"])
    resp = client.put(
        "/api/articles/has-tags",
        json={"article": {"tagList": []}},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["article"]["tagList"] == []


def test_update_article_null_tag_list_returns_422(client):
    token = _register(client)
    _create_article(client, token, title="Nulltag")
    resp = client.put(
        "/api/articles/nulltag",
        json={"article": {"tagList": None}},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_update_article_by_non_owner_returns_403(client):
    alice_token = _register(client, username="alice", email="alice@example.com")
    bob_token = _register(client, username="bob", email="bob@example.com")
    _create_article(client, alice_token, title="Alice's Post")
    resp = client.put(
        "/api/articles/alices-post",
        json={"article": {"title": "Hacked"}},
        headers=_auth(bob_token),
    )
    assert resp.status_code == 403
    assert resp.json()["errors"]["article"][0] == "forbidden"


# ── Delete ────────────────────────────────────────────────────────────────────


def test_delete_article_returns_204(client):
    token = _register(client)
    _create_article(client, token, title="Bye")
    resp = client.delete("/api/articles/bye", headers=_auth(token))
    assert resp.status_code == 204


def test_delete_article_then_get_returns_404(client):
    token = _register(client)
    _create_article(client, token, title="Gone")
    client.delete("/api/articles/gone", headers=_auth(token))
    resp = client.get("/api/articles/gone")
    assert resp.status_code == 404


def test_delete_article_by_non_owner_returns_403(client):
    alice_token = _register(client, username="alice", email="alice@example.com")
    bob_token = _register(client, username="bob", email="bob@example.com")
    _create_article(client, alice_token, title="Keep Mine")
    resp = client.delete("/api/articles/keep-mine", headers=_auth(bob_token))
    assert resp.status_code == 403
    assert resp.json()["errors"]["article"][0] == "forbidden"
