from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Alert, AlertStatus, NotificationDeliveryLog, User
from src.api.schemas import AnalyticsSummary

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/summary",
    response_model=AnalyticsSummary,
    summary="Analytics summary",
    description="Return basic analytics summary for the current user.",
)
def summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> AnalyticsSummary:
    total_alerts = db.query(Alert).filter(Alert.user_id == current_user.id).count()
    active_alerts = db.query(Alert).filter(Alert.user_id == current_user.id, Alert.status == AlertStatus.active).count()

    deliveries_total = db.query(NotificationDeliveryLog).filter(NotificationDeliveryLog.user_id == current_user.id).count()
    deliveries_sent = (
        db.query(NotificationDeliveryLog)
        .filter(NotificationDeliveryLog.user_id == current_user.id, NotificationDeliveryLog.status == "sent")
        .count()
    )
    deliveries_failed = (
        db.query(NotificationDeliveryLog)
        .filter(NotificationDeliveryLog.user_id == current_user.id, NotificationDeliveryLog.status == "failed")
        .count()
    )

    return AnalyticsSummary(
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        deliveries_total=deliveries_total,
        deliveries_sent=deliveries_sent,
        deliveries_failed=deliveries_failed,
    )
