from __future__ import annotations

from logging.config import fileConfig
from urllib.parse import urlparse

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.api.core.settings import get_settings
from src.api.models import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_sqlalchemy_url() -> str:
    """
    Build a SQLAlchemy URL for Alembic migrations.

    NOTE: In this environment POSTGRES_URL may be either a hostname (legacy) or a full URL
    (e.g. "postgresql://localhost:5000/myapp"). We normalize to host/port/db to ensure
    Alembic/SQLAlchemy can always parse the constructed DSN.
    """
    settings = get_settings()
    raw = (settings.postgres_url or "").strip()

    host = settings.postgres_url
    port = settings.postgres_port
    db = settings.postgres_db

    if "://" in raw:
        parsed = urlparse(raw)
        host = parsed.hostname or host
        port = str(parsed.port) if parsed.port is not None else port
        parsed_db = (parsed.path or "").lstrip("/")
        if parsed_db:
            db = parsed_db

    return f"postgresql+psycopg2://{settings.postgres_user}:{settings.postgres_password}@{host}:{port}/{db}"


def run_migrations_offline() -> None:
    url = _get_sqlalchemy_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _get_sqlalchemy_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
