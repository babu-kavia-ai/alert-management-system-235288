from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.core.db import engine
from src.api.core.security import hash_password
from src.api.core.settings import get_settings
from src.api.models import Base, User, UserRole
from src.api.routers import admin, alerts, analytics, auth, logs, notifications, preferences, templates
from src.api.schemas import HealthResponse

settings = get_settings()

openapi_tags = [
    {"name": "auth", "description": "Authentication and current user profile."},
    {"name": "alerts", "description": "CRUD for alerts, scheduling config, and manual trigger."},
    {"name": "templates", "description": "Reusable message templates."},
    {"name": "preferences", "description": "Per-user channel preferences."},
    {"name": "notifications", "description": "In-app inbox notifications."},
    {"name": "logs", "description": "Delivery attempt logs."},
    {"name": "analytics", "description": "Basic analytics summary."},
    {"name": "admin", "description": "Admin-only endpoints (users, scheduler run, stats)."},
]

app = FastAPI(
    title="Alert Management Backend API",
    description=(
        "Backend API for creating alerts, scheduling/recurrence, sending notifications via stub adapters "
        "(in-app/email/SMS/push), managing templates and preferences, and viewing logs/analytics.\n\n"
        "Auth: Use /auth/login to obtain a JWT and pass it as `Authorization: Bearer <token>`."
    ),
    version="0.1.0",
    openapi_tags=openapi_tags,
)

cors_origins = [o.strip() for o in settings.cors_allow_origins.split(",")] if settings.cors_allow_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    """
    Initialize database objects and optionally bootstrap an admin user.

    This creates tables if they don't exist (for local/dev), and if BOOTSTRAP_ADMIN_EMAIL/PASSWORD
    are set it will ensure that user exists with admin role.
    """
    # NOTE: In production, prefer Alembic migrations; this is a convenience for dev/CI.
    Base.metadata.create_all(bind=engine)

    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return

    from src.api.core.db import SessionLocal  # local import to avoid circular

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.bootstrap_admin_email).first()
        if not user:
            user = User(
                email=settings.bootstrap_admin_email,
                hashed_password=hash_password(settings.bootstrap_admin_password),
                role=UserRole.admin,
                is_active=True,
            )
            db.add(user)
        else:
            user.role = UserRole.admin
            user.is_active = True
        db.commit()
    finally:
        db.close()


@app.get(
    "/",
    response_model=HealthResponse,
    tags=["health"],
    summary="Health check",
    description="Simple health check endpoint.",
)
def health_check() -> HealthResponse:
    return HealthResponse(message="Healthy")


@app.get(
    "/docs/help",
    tags=["health"],
    summary="API usage help",
    description="Quick usage notes for authentication and key endpoints.",
)
def docs_help() -> dict:
    return {
        "auth": {
            "login": {"path": "/auth/login", "note": "POST email/password; use returned JWT in Authorization header."},
            "me": {"path": "/auth/me"},
        },
        "scheduling": {
            "note": "Use /admin/scheduler/run (admin) to process due alerts immediately in this stub implementation."
        },
    }


app.include_router(auth.router)
app.include_router(templates.router)
app.include_router(alerts.router)
app.include_router(preferences.router)
app.include_router(notifications.router)
app.include_router(logs.router)
app.include_router(analytics.router)
app.include_router(admin.router)
