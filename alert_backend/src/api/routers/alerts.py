from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.core.db import get_db
from src.api.deps import get_current_user
from src.api.models import Alert, Template, User
from src.api.schemas import AlertCreate, AlertOut, AlertUpdate
from src.api.services.dispatch import dispatch_alert
from src.api.services.scheduler import ensure_next_run_at

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _get_user_alert(db: Session, user_id: int, alert_id: int) -> Alert | None:
    return db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user_id).first()


@router.post(
    "",
    response_model=AlertOut,
    summary="Create alert",
    description="Create an alert with schedule and channel configuration.",
)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> AlertOut:
    if payload.template_id is not None:
        t = db.query(Template).filter(Template.id == payload.template_id).first()
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    a = Alert(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        channel=payload.channel,
        template_id=payload.template_id,
        status=payload.status,
        schedule_type=payload.schedule_type,
        schedule_config=payload.schedule_config,
    )
    ensure_next_run_at(a)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.get(
    "",
    response_model=list[AlertOut],
    summary="List alerts",
    description="List the current user's alerts.",
)
def list_alerts(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[AlertOut]:
    return (
        db.query(Alert)
        .filter(Alert.user_id == current_user.id)
        .order_by(Alert.created_at.desc())
        .all()
    )


@router.get(
    "/{alert_id}",
    response_model=AlertOut,
    summary="Get alert",
    description="Get an alert by id (owned by current user).",
)
def get_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> AlertOut:
    a = _get_user_alert(db, current_user.id, alert_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return a


@router.patch(
    "/{alert_id}",
    response_model=AlertOut,
    summary="Update alert",
    description="Update an alert by id (owned by current user). Recomputes next_run_at if schedule changes.",
)
def update_alert(
    alert_id: int,
    payload: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AlertOut:
    a = _get_user_alert(db, current_user.id, alert_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    data = payload.model_dump(exclude_unset=True)
    if "template_id" in data and data["template_id"] is not None:
        t = db.query(Template).filter(Template.id == data["template_id"]).first()
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    for field, value in data.items():
        setattr(a, field, value)

    if any(k in data for k in ("schedule_type", "schedule_config")):
        ensure_next_run_at(a)

    db.commit()
    db.refresh(a)
    return a


@router.delete(
    "/{alert_id}",
    status_code=204,
    summary="Delete alert",
    description="Delete an alert by id (owned by current user).",
)
def delete_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> None:
    a = _get_user_alert(db, current_user.id, alert_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    db.delete(a)
    db.commit()
    return None


@router.post(
    "/{alert_id}/trigger",
    summary="Trigger alert now",
    description="Manually trigger an alert immediately (writes delivery log and in-app notification if applicable).",
)
def trigger_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> dict:
    a = _get_user_alert(db, current_user.id, alert_id)
    if not a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    rendered = {"title": f"Alert: {a.name}", "message": a.description or "", "body": a.description or ""}
    log = dispatch_alert(db, current_user, a, rendered)
    db.commit()
    db.refresh(log)
    return {"status": "ok", "delivery_log_id": log.id}
