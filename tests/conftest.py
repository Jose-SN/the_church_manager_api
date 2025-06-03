import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret")
