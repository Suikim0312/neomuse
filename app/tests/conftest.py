"""Pytest fixtures: isolated SQLite test database and HTTP client."""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_app.db")

from app.db.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DB_URL = "sqlite:///./test_app.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def register_and_login(client, email="t@test.local", password="secret123",
                       role="visitor", full_name="Test User"):
    client.post("/api/auth/register", json={
        "full_name": full_name, "email": email,
        "password": password, "role": role,
    })
    resp = client.post("/api/auth/login-json", json={
        "email": email, "password": password,
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
