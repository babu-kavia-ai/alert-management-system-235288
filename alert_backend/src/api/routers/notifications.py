from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Notification, User
from src.api.schemas import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "",
    response_model=list[NotificationOut],
    summary="List notifications",
    description="List current user's in-app inbox notifications (newest first).",
)
def list_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[NotificationOut]:
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.post(
    "/{notification_id}/read",
    response_model=NotificationOut,
    summary="Mark notification as read",
    description="Mark a notification as read.",
)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationOut:
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    n.is_read = True
    db.commit()
    db.refresh(n)
    return n
