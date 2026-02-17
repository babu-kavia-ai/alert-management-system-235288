from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dateutil import parser
from sqlalchemy.orm import Session

from src.api.models import Alert, AlertStatus, User
from src.api.services.dispatch import dispatch_alert


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _compute_next_run(alert: Alert, now: datetime) -> datetime | None:
    """Compute next_run_at from schedule_type/config. Returns None if no next run."""
    cfg = alert.schedule_config or {}
    st = alert.schedule_type

    if st == "one_time":
        run_at = cfg.get("run_at")
        if not run_at:
            return None
        dt = parser.isoparse(run_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    if st == "interval":
        # cfg: {"every_minutes": 15} OR {"every_seconds": 30}
        every_seconds = cfg.get("every_seconds")
        every_minutes = cfg.get("every_minutes")
        seconds = int(every_seconds or 0) + int(every_minutes or 0) * 60
        if seconds <= 0:
            return None
        return now + timedelta(seconds=seconds)

    if st == "cron":
        # Minimal stub: daily at HH:MM in UTC (no full cron parser to keep deps small)
        # cfg: {"hour": 9, "minute": 30}
        hour = int(cfg.get("hour", 0))
        minute = int(cfg.get("minute", 0))
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate = candidate + timedelta(days=1)
        return candidate

    return None


# PUBLIC_INTERFACE
def ensure_next_run_at(alert: Alert) -> None:
    """Ensure next_run_at is populated based on current schedule config."""
    now = _utcnow()
    alert.next_run_at = _compute_next_run(alert, now)


# PUBLIC_INTERFACE
def process_due_alerts(db: Session, limit: int = 50) -> int:
    """Find due alerts and dispatch them (stub), updating next_run_at/last_run_at and writing logs."""
    now = _utcnow()

    due = (
        db.query(Alert)
        .filter(Alert.status == AlertStatus.active)
        .filter(Alert.next_run_at.isnot(None))
        .filter(Alert.next_run_at <= now)
        .order_by(Alert.next_run_at.asc())
        .limit(limit)
        .all()
    )

    processed = 0
    for alert in due:
        user: User | None = db.query(User).filter(User.id == alert.user_id).first()
        if not user or not user.is_active:
            alert.next_run_at = None
            processed += 1
            continue

        rendered = {"title": f"Alert: {alert.name}", "message": alert.description or "", "body": alert.description or ""}

        dispatch_alert(db, user, alert, rendered)

        alert.last_run_at = now
        # compute next:
        next_dt = _compute_next_run(alert, now)
        if alert.schedule_type == "one_time":
            # one-time consumes schedule
            alert.next_run_at = None
        else:
            alert.next_run_at = next_dt
        processed += 1

    return processed
