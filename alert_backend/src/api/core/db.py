from __future__ import annotations

from collections.abc import Generator
from urllib.parse import urlparse

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.settings import get_settings

settings = get_settings()


def _normalize_postgres_parts() -> tuple[str, str, str]:
    """
    Normalize postgres host/port/db from settings.

    Supports two patterns for POSTGRES_URL:
    1) host only (e.g. "localhost")
    2) full URL (e.g. "postgresql://user:pass@localhost:5000/mydb")

    Returns:
        (host, port, db)
    """
    raw = (settings.postgres_url or "").strip()

    # If POSTGRES_URL is actually a full URL, prefer its parsed parts.
    if "://" in raw:
        parsed = urlparse(raw)
        host = parsed.hostname or settings.postgres_url
        port = str(parsed.port) if parsed.port is not None else settings.postgres_port
        db = (parsed.path or "").lstrip("/") or settings.postgres_db
        return host, port, db

    return settings.postgres_url, settings.postgres_port, settings.postgres_db


pg_host, pg_port, pg_db = _normalize_postgres_parts()

# Build SQLAlchemy URL from normalized parts.
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}"
    f"@{pg_host}:{pg_port}/{pg_db}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session and ensures it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
