"""
Database connection, engine configuration, and session management.
"""
from contextlib import contextmanager
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from libscope.core.config import get_settings
from libscope.core.logging import get_logger
from libscope.core.models import Base

logger = get_logger("database")

_engine = None
_SessionFactory = None


def get_engine():
    """Get or initialize the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url

        # Ensure sqlite parent directory exists
        if db_url.startswith("sqlite:///"):
            sqlite_path = db_url.replace("sqlite:///", "")
            # Handle relative vs absolute paths
            p = Path(sqlite_path)
            if not p.is_absolute():
                p = Path.cwd() / p
            p.parent.mkdir(parents=True, exist_ok=True)
            db_url = f"sqlite:///{p.resolve()}"

            _engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                echo=settings.debug,
            )

            # Enable foreign keys for SQLite
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()

        else:
            # PostgreSQL or standard external RDBMS
            _engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.debug,
            )

        logger.info(f"Initialized database engine for {db_url.split('@')[-1] if '@' in db_url else db_url}")
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get or initialize the sessionmaker."""
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionFactory


def init_db() -> None:
    """Create all database tables if they do not already exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully")


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic commit/rollback."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.error(f"Database session rolled back due to error: {exc}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session injection."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        session.close()

