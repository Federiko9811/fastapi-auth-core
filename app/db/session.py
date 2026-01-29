"""
Database session management.

Provides async database engine, session factory, and dependency injection.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Build database connection URL (postgresql+asyncpg://user:pass@host:port/db)
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)

# Create async database engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # Set to True to log SQL queries (debugging)
)

# Create session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """
    Dependency injection for database sessions.

    Provides a database session for each request that is automatically
    closed when the request completes.

    Yields:
        AsyncSession: An async database session.
    """
    async with SessionLocal() as session:
        yield session
