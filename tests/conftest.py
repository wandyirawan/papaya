from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.main import app
from app.db.database import get_session
import pytest_asyncio


@pytest_asyncio.fixture
def test_app():
    """Create test application."""
    return app


@pytest_asyncio.fixture
async def client(test_app):
    """Create test client."""
    from httpx import ASGITransport
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    """Create test database session."""
    async for session in get_session():
        yield session
