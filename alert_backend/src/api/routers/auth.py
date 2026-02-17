from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.core.security import create_access_token, hash_password, verify_password
from src.api.deps import get_current_user
from src.api.models import User, UserRole
from src.api.schemas import TokenResponse, UserCreate, UserLogin, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    summary="Register a new user",
    description="Create a new user account with default role=user.",
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserPublic:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password), role=UserRole.user)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Login with email/password and receive a JWT access token.",
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=user.email, role=user.role.value)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=UserPublic,
    summary="Get current user",
    description="Return the current authenticated user's profile.",
)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return current_user
