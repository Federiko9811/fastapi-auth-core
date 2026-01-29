"""
Pytest configuration and fixtures.

Uses a dedicated test database that is created before tests
and cleaned up after tests complete.
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db

# Import all models so they are registered with Base.metadata
from app.models.user import User  # noqa: F401

# Test database name - separate from development/production
TEST_DB_NAME = f"{settings.POSTGRES_DB}_test"

# URL to connect to postgres (without specific database) for creating test db
POSTGRES_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/postgres"
)

# URL for the test database
TEST_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{TEST_DB_NAME}"
)


def run_async(coro):
    """Run async function synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _create_test_database() -> None:
    """Create the test database if it doesn't exist."""
    engine = create_async_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        # Check if database exists
        result = await conn.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname = '{TEST_DB_NAME}'")
        )
        exists = result.scalar() is not None

        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))

    await engine.dispose()


async def _drop_test_database() -> None:
    """Drop the test database."""
    engine = create_async_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        # Terminate existing connections
        await conn.execute(
            text(
                f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
                AND pid <> pg_backend_pid()
                """
            )
        )
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"'))

    await engine.dispose()


async def _create_tables() -> None:
    """Create all tables in test database."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """
    Create test database before tests, drop it after.

    This fixture runs automatically for the entire test session.
    """
    # Setup: Create test database and tables
    run_async(_create_test_database())
    run_async(_create_tables())

    yield  # Run tests

    # Teardown: Drop test database
    run_async(_drop_test_database())


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for tests."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client with test database."""
    # Import here to avoid circular imports
    from app.main import app

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
