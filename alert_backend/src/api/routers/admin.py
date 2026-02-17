from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import require_admin
from src.api.models import Alert, NotificationDeliveryLog, User
from src.api.schemas import UserPublic
from src.api.services.scheduler import process_due_alerts

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/users",
    response_model=list[UserPublic],
    summary="List users (admin)",
    description="List all users (admin only).",
)
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> list[UserPublic]:
    return db.query(User).order_by(User.created_at.desc()).all()


@router.post(
    "/scheduler/run",
    summary="Run scheduler processing (admin)",
    description="Process due alerts immediately. Intended for admin/testing; production would run on a background schedule.",
)
def run_scheduler(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    processed = process_due_alerts(db)
    db.commit()
    return {"processed": processed}


@router.get(
    "/stats",
    summary="Admin stats",
    description="Return basic admin-level counts.",
)
def admin_stats(db: Session = Depends(get_db), _: User = Depends(require_admin)) -> dict:
    users = db.query(User).count()
    alerts = db.query(Alert).count()
    deliveries = db.query(NotificationDeliveryLog).count()
    return {"users": users, "alerts": alerts, "deliveries": deliveries}
