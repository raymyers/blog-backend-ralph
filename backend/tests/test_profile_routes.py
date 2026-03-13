"""Route behavior: profile endpoints."""

from fastapi.testclient import TestClient


def _register(client: TestClient, username="alice", email="alice@example.com"):
    resp = client.post(
        "/api/users",
        json={"user": {"username": username, "email": email, "password": "s3cret"}},
    )
    return resp.json()["user"]["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


# ── Get Profile ────────────────────────────────────────────────────────────────


def test_get_profile_returns_username(client):
    _register(client, username="alice", email="alice@example.com")
    resp = client.get("/api/profiles/alice")
    assert resp.status_code == 200
    assert resp.json()["profile"]["username"] == "alice"


def test_get_profile_unknown_user_returns_404(client):
    resp = client.get("/api/profiles/no-such-user")
    assert resp.status_code == 404
    assert resp.json()["errors"]["profile"][0] == "not found"


def test_get_profile_unauthenticated_shows_not_following(client):
    _register(client, username="alice", email="alice@example.com")
    resp = client.get("/api/profiles/alice")
    assert resp.json()["profile"]["following"] is False


def test_get_profile_authenticated_shows_following_status(client):
    _register(client, username="alice", email="alice@example.com")
    bob_token = _register(client, username="bob", email="bob@example.com")
    # Bob hasn't followed alice yet
    resp = client.get("/api/profiles/alice", headers=_auth(bob_token))
    assert resp.json()["profile"]["following"] is False


# ── Follow ─────────────────────────────────────────────────────────────────────


def test_follow_user_returns_following_true(client):
    _register(client, username="alice", email="alice@example.com")
    bob_token = _register(client, username="bob", email="bob@example.com")
    resp = client.post("/api/profiles/alice/follow", headers=_auth(bob_token))
    assert resp.status_code == 200
    assert resp.json()["profile"]["following"] is True


def test_follow_unknown_user_returns_404(client):
    bob_token = _register(client, username="bob", email="bob@example.com")
    resp = client.post("/api/profiles/ghost/follow", headers=_auth(bob_token))
    assert resp.status_code == 404
    assert resp.json()["errors"]["profile"][0] == "not found"


def test_follow_requires_auth(client):
    _register(client, username="alice", email="alice@example.com")
    resp = client.post("/api/profiles/alice/follow")
    assert resp.status_code == 401


# ── Unfollow ───────────────────────────────────────────────────────────────────


def test_unfollow_user_returns_following_false(client):
    _register(client, username="alice", email="alice@example.com")
    bob_token = _register(client, username="bob", email="bob@example.com")
    client.post("/api/profiles/alice/follow", headers=_auth(bob_token))
    resp = client.delete("/api/profiles/alice/follow", headers=_auth(bob_token))
    assert resp.status_code == 200
    assert resp.json()["profile"]["following"] is False


def test_get_profile_after_follow_shows_following_true(client):
    _register(client, username="alice", email="alice@example.com")
    bob_token = _register(client, username="bob", email="bob@example.com")
    client.post("/api/profiles/alice/follow", headers=_auth(bob_token))
    resp = client.get("/api/profiles/alice", headers=_auth(bob_token))
    assert resp.json()["profile"]["following"] is True
