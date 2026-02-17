from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field

from src.api.models import AlertStatus, ChannelType, UserRole


class HealthResponse(BaseModel):
    message: str = Field(..., description="Health status message.")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field("bearer", description="Token type (always 'bearer').")


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email.")
    password: str = Field(..., min_length=8, description="User password.")


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="User email.")
    password: str = Field(..., description="User password.")


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Template name.")
    description: str | None = Field(None, max_length=500, description="Optional template description.")
    subject: str | None = Field(None, max_length=250, description="Optional subject line (email/push).")
    body: str = Field(..., min_length=1, description="Template body.")
    metadata_json: dict[str, Any] = Field(default_factory=dict, description="Arbitrary JSON metadata.")


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    subject: str | None = Field(None, max_length=250)
    body: str | None = Field(None, min_length=1)
    metadata_json: dict[str, Any] | None = None


class TemplateOut(BaseModel):
    id: int
    name: str
    description: str | None
    subject: str | None
    body: str
    metadata_json: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


ScheduleType = Literal["one_time", "interval", "cron"]


class AlertCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    channel: ChannelType = Field(..., description="Delivery channel for this alert.")
    template_id: int | None = Field(None, description="Optional template for message content.")
    status: AlertStatus = Field(AlertStatus.active, description="Initial alert status.")
    schedule_type: ScheduleType = Field("one_time", description="Scheduling mode.")
    schedule_config: dict[str, Any] = Field(default_factory=dict, description="Schedule configuration.")


class AlertUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    channel: ChannelType | None = None
    template_id: int | None = None
    status: AlertStatus | None = None
    schedule_type: ScheduleType | None = None
    schedule_config: dict[str, Any] | None = None


class AlertOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: str | None
    status: AlertStatus
    channel: ChannelType
    template_id: int | None
    schedule_type: str
    schedule_config: dict[str, Any]
    next_run_at: datetime | None
    last_run_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class PreferenceUpsert(BaseModel):
    channel: ChannelType = Field(..., description="Channel to configure.")
    enabled: bool = Field(..., description="Whether this channel is enabled.")
    config: dict[str, Any] = Field(default_factory=dict, description="Optional per-channel config.")


class PreferenceOut(BaseModel):
    id: int
    user_id: int
    channel: ChannelType
    enabled: bool
    config: dict[str, Any]

    class Config:
        from_attributes = True


class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    related_alert_id: int | None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DeliveryLogOut(BaseModel):
    id: int
    user_id: int
    alert_id: int | None
    channel: ChannelType
    status: str
    provider_message_id: str | None
    error: str | None
    payload: dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsSummary(BaseModel):
    total_alerts: int = Field(..., description="Total alerts.")
    active_alerts: int = Field(..., description="Active alerts.")
    deliveries_total: int = Field(..., description="Total delivery attempts.")
    deliveries_sent: int = Field(..., description="Delivery attempts with status=sent.")
    deliveries_failed: int = Field(..., description="Delivery attempts with status=failed.")
