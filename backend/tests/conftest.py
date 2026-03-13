"""Shared test fixtures."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine

import app.adapters.database  # noqa: F401 — registers SQLModel table metadata
import app.deps as deps
from app.main import app as fastapi_app


@pytest.fixture()
def client():
    """TestClient backed by an isolated in-memory SQLite database.

    Uses StaticPool so all connections share the same in-memory database.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    deps._test_engine = engine
    with TestClient(fastapi_app, raise_server_exceptions=True) as c:
        yield c
    deps._test_engine = None
    SQLModel.metadata.drop_all(engine)
