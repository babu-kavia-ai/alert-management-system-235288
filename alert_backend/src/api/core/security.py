from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from src.api.core.settings import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# PUBLIC_INTERFACE
def create_access_token(subject: str, role: str, expires_minutes: int | None = None) -> str:
    """Create a JWT access token for a user (subject=email) including role claim."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_access_token_expire_minutes
    )
    payload: dict[str, Any] = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# PUBLIC_INTERFACE
def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises jwt exceptions if invalid/expired."""
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
