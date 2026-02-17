from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session

from src.api.models import Alert, ChannelType, Notification, NotificationDeliveryLog, User


@dataclass
class DispatchResult:
    status: str
    provider_message_id: str | None = None
    error: str | None = None
    payload: dict | None = None


class ChannelAdapter(Protocol):
    """Adapter interface for sending a notification via a channel."""

    def send(self, user: User, alert: Alert, rendered: dict) -> DispatchResult: ...


class EmailAdapter:
    """Stub email adapter."""

    def send(self, user: User, alert: Alert, rendered: dict) -> DispatchResult:
        return DispatchResult(status="sent", provider_message_id="stub-email-1", payload=rendered)


class SMSAdapter:
    """Stub SMS adapter."""

    def send(self, user: User, alert: Alert, rendered: dict) -> DispatchResult:
        return DispatchResult(status="sent", provider_message_id="stub-sms-1", payload=rendered)


class PushAdapter:
    """Stub push adapter."""

    def send(self, user: User, alert: Alert, rendered: dict) -> DispatchResult:
        return DispatchResult(status="sent", provider_message_id="stub-push-1", payload=rendered)


class InAppAdapter:
    """In-app adapter writes to Notification inbox."""

    def __init__(self, db: Session):
        self.db = db

    def send(self, user: User, alert: Alert, rendered: dict) -> DispatchResult:
        n = Notification(
            user_id=user.id,
            title=rendered.get("title") or f"Alert: {alert.name}",
            message=rendered.get("message") or rendered.get("body") or "",
            related_alert_id=alert.id,
        )
        self.db.add(n)
        return DispatchResult(status="sent", provider_message_id=None, payload=rendered)


# PUBLIC_INTERFACE
def dispatch_alert(db: Session, user: User, alert: Alert, rendered: dict) -> NotificationDeliveryLog:
    """Dispatch an alert via its configured channel using stub adapters, and persist a delivery log."""
    if alert.channel == ChannelType.email:
        adapter: ChannelAdapter = EmailAdapter()
    elif alert.channel == ChannelType.sms:
        adapter = SMSAdapter()
    elif alert.channel == ChannelType.push:
        adapter = PushAdapter()
    else:
        adapter = InAppAdapter(db)

    try:
        result = adapter.send(user, alert, rendered)
    except Exception as e:
        result = DispatchResult(status="failed", error=str(e), payload=rendered)

    log = NotificationDeliveryLog(
        user_id=user.id,
        alert_id=alert.id,
        channel=alert.channel,
        status=result.status,
        provider_message_id=result.provider_message_id,
        error=result.error,
        payload=result.payload or rendered,
    )
    db.add(log)
    return log
