from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database (provided by alert_database container)
    postgres_url: str = Field(..., alias="POSTGRES_URL", description="PostgreSQL host/address (not a full SQLAlchemy URL).")
    postgres_user: str = Field(..., alias="POSTGRES_USER", description="PostgreSQL username.")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD", description="PostgreSQL password.")
    postgres_db: str = Field(..., alias="POSTGRES_DB", description="PostgreSQL database name.")
    postgres_port: str = Field(..., alias="POSTGRES_PORT", description="PostgreSQL port.")

    # Security
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY", description="Secret key used to sign JWTs.")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM", description="JWT signing algorithm.")
    jwt_access_token_expire_minutes: int = Field(
        60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES", description="Access token lifetime in minutes."
    )

    # Bootstrap admin
    bootstrap_admin_email: str | None = Field(
        None, alias="BOOTSTRAP_ADMIN_EMAIL", description="Optional email for bootstrap admin user."
    )
    bootstrap_admin_password: str | None = Field(
        None, alias="BOOTSTRAP_ADMIN_PASSWORD", description="Optional password for bootstrap admin user."
    )

    # CORS
    cors_allow_origins: str = Field("*", alias="CORS_ALLOW_ORIGINS", description="Comma-separated list or '*'.")


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Return application settings loaded from environment variables."""
    return Settings()
