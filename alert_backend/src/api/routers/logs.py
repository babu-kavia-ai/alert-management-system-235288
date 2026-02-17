from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import NotificationDeliveryLog, User
from src.api.schemas import DeliveryLogOut

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get(
    "/deliveries",
    response_model=list[DeliveryLogOut],
    summary="List delivery logs",
    description="List delivery logs for the current user (newest first).",
)
def list_delivery_logs(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[DeliveryLogOut]:
    return (
        db.query(NotificationDeliveryLog)
        .filter(NotificationDeliveryLog.user_id == current_user.id)
        .order_by(NotificationDeliveryLog.created_at.desc())
        .limit(500)
        .all()
    )
