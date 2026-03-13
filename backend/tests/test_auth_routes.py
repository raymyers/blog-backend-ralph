"""Route behavior: auth endpoints (Milestone 1)."""

from fastapi.testclient import TestClient


def register(client: TestClient, username="alice", email="alice@example.com", password="s3cret"):
    return client.post(
        "/api/users",
        json={"user": {"username": username, "email": email, "password": password}},
    )


def login(client: TestClient, email="alice@example.com", password="s3cret"):
    return client.post("/api/users/login", json={"user": {"email": email, "password": password}})


# ── Registration ────────────────────────────────────────────────────────────


def test_register_returns_201(client):
    resp = register(client)
    assert resp.status_code == 201


def test_register_returns_user_data(client):
    resp = register(client)
    assert resp.json()["user"]["username"] == "alice"
    assert resp.json()["user"]["email"] == "alice@example.com"
    assert resp.json()["user"]["bio"] is None
    assert resp.json()["user"]["image"] is None


def test_register_returns_token(client):
    resp = register(client)
    assert resp.json()["user"]["token"] != ""


def test_register_blank_username_returns_422(client):
    resp = register(client, username="")
    assert resp.status_code == 422


def test_register_blank_email_returns_422(client):
    resp = register(client, email="")
    assert resp.status_code == 422


def test_register_blank_password_returns_422(client):
    resp = register(client, password="")
    assert resp.status_code == 422


def test_register_duplicate_email_returns_409(client):
    register(client)
    resp = register(client, username="other")
    assert resp.status_code == 409
    assert resp.json()["errors"]["email"][0] == "has already been taken"


def test_register_duplicate_username_returns_409(client):
    register(client)
    resp = register(client, email="other@example.com")
    assert resp.status_code == 409
    assert resp.json()["errors"]["username"][0] == "has already been taken"


# ── Login ───────────────────────────────────────────────────────────────────


def test_login_returns_200(client):
    register(client)
    resp = login(client)
    assert resp.status_code == 200


def test_login_returns_user_data(client):
    register(client)
    resp = login(client)
    assert resp.json()["user"]["email"] == "alice@example.com"


def test_login_wrong_password_returns_401(client):
    register(client)
    resp = login(client, password="wrongpassword")
    assert resp.status_code == 401
    assert resp.json()["errors"]["credentials"][0] == "invalid"


def test_login_blank_email_returns_422(client):
    resp = login(client, email="")
    assert resp.status_code == 422
    assert resp.json()["errors"]["email"][0] == "can't be blank"


def test_login_blank_password_returns_422(client):
    register(client)
    resp = login(client, password="")
    assert resp.status_code == 422
    assert resp.json()["errors"]["password"][0] == "can't be blank"


# ── Get current user ─────────────────────────────────────────────────────────


def test_get_user_returns_200(client):
    register(client)
    token = login(client).json()["user"]["token"]
    resp = client.get("/api/user", headers={"Authorization": f"Token {token}"})
    assert resp.status_code == 200


def test_get_user_returns_current_user(client):
    register(client)
    token = login(client).json()["user"]["token"]
    resp = client.get("/api/user", headers={"Authorization": f"Token {token}"})
    assert resp.json()["user"]["username"] == "alice"


def test_get_user_no_token_returns_401(client):
    resp = client.get("/api/user")
    assert resp.status_code == 401
    assert resp.json()["errors"]["token"][0] == "is missing"


def test_put_user_no_token_returns_401(client):
    resp = client.put("/api/user", json={"user": {"bio": "test"}})
    assert resp.status_code == 401
    assert resp.json()["errors"]["token"][0] == "is missing"


# ── Update user ──────────────────────────────────────────────────────────────


def test_update_user_bio(client):
    register(client)
    token = login(client).json()["user"]["token"]
    resp = client.put(
        "/api/user",
        json={"user": {"bio": "Updated bio"}},
        headers={"Authorization": f"Token {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["bio"] == "Updated bio"


def test_update_user_bio_empty_string_normalizes_to_null(client):
    register(client)
    token = login(client).json()["user"]["token"]
    client.put("/api/user", json={"user": {"bio": "A bio"}}, headers={"Authorization": f"Token {token}"})
    resp = client.put("/api/user", json={"user": {"bio": ""}}, headers={"Authorization": f"Token {token}"})
    assert resp.json()["user"]["bio"] is None


def test_update_user_email_empty_returns_422(client):
    register(client)
    token = login(client).json()["user"]["token"]
    resp = client.put("/api/user", json={"user": {"email": ""}}, headers={"Authorization": f"Token {token}"})
    assert resp.status_code == 422


def test_update_user_username_empty_returns_422(client):
    register(client)
    token = login(client).json()["user"]["token"]
    resp = client.put("/api/user", json={"user": {"username": ""}}, headers={"Authorization": f"Token {token}"})
    assert resp.status_code == 422
