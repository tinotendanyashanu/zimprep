"""Database connection and session management.

Provides async SQLAlchemy session with connection pooling and error handling.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.exc import SQLAlchemyError

from app.config.settings import settings
from app.engines.identity_subscription.errors import DatabaseError

logger = logging.getLogger(__name__)

# Global engine instance (lazy initialization)
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine.
    
    Connection pooling configuration:
    - Pool size: 10 connections
    - Max overflow: 20 additional connections
    - Pool recycle: 3600 seconds (1 hour)
    """
    global _engine
    
    if _engine is None:
        # For PostgreSQL with asyncpg
        database_url = getattr(settings, "DATABASE_URL", "")
        
        if not database_url:
            logger.warning("DATABASE_URL not configured, using in-memory SQLite")
            database_url = "sqlite+aiosqlite:///:memory:"
        
        # Ensure async driver
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1
            )
        
        _engine = create_async_engine(
            database_url,
            echo=False,  # Set to True for SQL query logging
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            pool_pre_ping=True,  # Validate connections before use
        )
        
        logger.info(f"Database engine created: {database_url.split('@')[-1]}")
    
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    
    return _session_factory


@asynccontextmanager
async def get_session(
    trace_id: str | None = None
) -> AsyncGenerator[AsyncSession, None]:
    """Get an async database session.
    
    Args:
        trace_id: Optional trace ID for error logging
    
    Yields:
        AsyncSession for database operations
    
    Raises:
        DatabaseError: If session creation or commit fails
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(
            f"Database error in session",
            extra={"trace_id": trace_id, "error": str(e)},
        )
        raise DatabaseError(
            message=f"Database operation failed: {str(e)}",
            trace_id=trace_id,
            metadata={"error_type": type(e).__name__},
        )
    finally:
        await session.close()


async def close_engine():
    """Close the database engine (cleanup on shutdown)."""
    global _engine, _session_factory
    
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine closed")
