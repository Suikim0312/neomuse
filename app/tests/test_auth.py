from app.tests.conftest import register_and_login


def test_register(client):
    resp = client.post("/api/auth/register", json={
        "full_name": "Иван Иванов",
        "email": "ivan@test.local",
        "password": "secret123",
        "role": "visitor",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "ivan@test.local"
    assert "hashed_password" not in data


def test_login_and_me(client):
    headers = register_and_login(client, email="login@test.local")
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "login@test.local"


def test_protected_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_login_wrong_password(client):
    register_and_login(client, email="x@test.local", password="secret123")
    resp = client.post("/api/auth/login-json", json={
        "email": "x@test.local", "password": "wrong",
    })
    assert resp.status_code == 401
