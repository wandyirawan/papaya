from sqlmodel import SQLModel, Field, create_engine, Session, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import aiosqlite

from app.config import get_settings

# Global engine variable
engine = None


def init_engine():
    """Initialize database engine."""
    global engine
    settings = get_settings()
    # Convert sqlite:/// to sqlite+aiosqlite:/// for async
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")
    engine = create_async_engine(db_url, echo=False)
    return engine


async def init_db():
    """Create database tables."""
    global engine
    if engine is None:
        engine = init_engine()
    from app.db.models import Recommendation, WeatherCache
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    global engine
    if engine is None:
        engine = init_engine()
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@asynccontextmanager
async def get_session_context():
    """Context manager for database sessions."""
    async for session in get_session():
        yield session
