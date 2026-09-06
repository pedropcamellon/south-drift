"""Database configuration for user management."""

import logging
from collections.abc import AsyncGenerator
from typing import cast

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

logger = logging.getLogger(__name__)

DATABASE_URL = cast(str, settings.model_dump()["database_url"])
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is required. "
        "Expected format: postgresql+asyncpg://user:pass@host:port/dbname"
    )

if not DATABASE_URL.startswith("postgresql"):
    raise ValueError(f"Only PostgreSQL is supported. Got: {DATABASE_URL.split('://')[0]}")

# PostgreSQL async engine with connection pooling
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Async session maker
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


def _mask_password(url: str) -> str:
    """Mask password in database URL for safe logging."""
    if "@" not in url:
        return url
    try:
        parts = url.split(":")
        password_part = parts[2].split("@")[0]
        return url.replace(password_part, "***")
    except (IndexError, AttributeError):
        return url


def _log_connection_error(error: Exception) -> None:
    """Log detailed database connection error with troubleshooting steps."""
    error_type = type(error).__name__
    error_msg = str(error)

    logger.error("=" * 70)
    logger.error("DATABASE CONNECTION FAILED")
    logger.error("=" * 70)

    if "gaierror" in error_type or "Name or service not known" in error_msg:
        db_host = DATABASE_URL.split("@")[1].split("/")[0] if "@" in DATABASE_URL else "unknown"
        logger.error(f"Cannot resolve database hostname: {db_host}")
        logger.error("")
        logger.error("Possible causes:")
        logger.error("  • PostgreSQL container is not running")
        logger.error("  • Incorrect hostname in DATABASE_URL")
        logger.error("  • Network issue between containers")
        logger.error("")
        logger.error("Quick fixes:")
        logger.error("  1. Check if postgres container is running: docker ps")
        logger.error("  2. Verify DATABASE_URL in docker-compose.yml")
        logger.error("  3. Try: docker compose restart postgres")
    elif "could not connect" in error_msg.lower() or "connection refused" in error_msg.lower():
        logger.error("Database server refused connection")
        logger.error("")
        logger.error("Possible causes:")
        logger.error("  • PostgreSQL is not ready yet")
        logger.error("  • Wrong port number")
        logger.error("  • Firewall blocking connection")
    elif "password authentication failed" in error_msg.lower():
        logger.error("Authentication failed - wrong username or password")
        logger.error("")
        logger.error("Check DATABASE_URL credentials in docker-compose.yml")
    elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
        logger.error("Database does not exist")
        logger.error("")
        logger.error("PostgreSQL is running but the database hasn't been created")
    else:
        logger.error(f"Unexpected error: {error_type}")
        logger.error(f"Details: {error_msg[:200]}")

    logger.error("")
    logger.error(f"Current DATABASE_URL: {_mask_password(DATABASE_URL)}")
    logger.error("=" * 70)


async def verify_database_connection() -> None:
    """Verify the Alembic-managed database is reachable."""
    try:
        logger.info("Connecting to database...")
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("Database connection verified")
    except Exception as exc:
        _log_connection_error(exc)
        raise RuntimeError("Database initialization failed") from exc


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """Dependency for getting user database."""
    from app.models.user import User

    yield SQLAlchemyUserDatabase(session, User)
