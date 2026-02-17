from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class ChannelType(str, enum.Enum):
    in_app = "in_app"
    email = "email"
    sms = "sms"
    push = "push"


class AlertStatus(str, enum.Enum):
    active = "active"
    paused = "paused"
    archived = "archived"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    alerts = relationship("Alert", back_populates="user", cascade="all,delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", cascade="all,delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all,delete-orphan")


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Generic template fields. Dispatch adapters interpret them per channel.
    subject: Mapped[str | None] = mapped_column(String(250), nullable=True)
    body: Mapped[str] = mapped_column(Text)

    # Optional structured metadata (e.g. variables, formatting settings)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    alerts = relationship("Alert", back_populates="template")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.active, index=True)

    channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType), index=True)
    template_id: Mapped[int | None] = mapped_column(ForeignKey("templates.id"), nullable=True)

    # Scheduling
    schedule_type: Mapped[str] = mapped_column(
        String(40), default="one_time", index=True
    )  # one_time | interval | cron
    schedule_config: Mapped[dict] = mapped_column(JSON, default=dict)  # e.g. {"run_at": "..."} or interval/cron dict
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")
    template = relationship("Template", back_populates="alerts")
    deliveries = relationship("NotificationDeliveryLog", back_populates="alert")


class UserPreference(Base):
    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "channel", name="uq_user_channel_pref"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Optional channel config (e.g. phone number, push token)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="preferences")


class Notification(Base):
    """In-app notification/inbox item."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    related_alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True, index=True)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class NotificationDeliveryLog(Base):
    """Delivery log for attempted sends across channels (including stub adapters)."""

    __tablename__ = "notification_delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    alert_id: Mapped[int | None] = mapped_column(ForeignKey("alerts.id"), nullable=True, index=True)

    channel: Mapped[ChannelType] = mapped_column(Enum(ChannelType), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)  # sent|failed|queued|skipped
    provider_message_id: Mapped[str | None] = mapped_column(String(200), nullable=True)

    error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    alert = relationship("Alert", back_populates="deliveries")
