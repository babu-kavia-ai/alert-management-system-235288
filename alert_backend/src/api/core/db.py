from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.api.core.settings import get_settings

settings = get_settings()

# Build SQLAlchemy URL from provided discrete env vars.
SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_url}:{settings.postgres_port}/{settings.postgres_db}"
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
