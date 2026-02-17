"""init

Revision ID: 0001_init
Revises: 
Create Date: 2026-02-17

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("user", "admin", name="userrole"), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "templates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("subject", sa.String(length=250), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_templates_name", "templates", ["name"])

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("status", sa.Enum("active", "paused", "archived", name="alertstatus"), nullable=False),
        sa.Column("channel", sa.Enum("in_app", "email", "sms", "push", name="channeltype"), nullable=False),
        sa.Column("template_id", sa.Integer(), sa.ForeignKey("templates.id"), nullable=True),
        sa.Column("schedule_type", sa.String(length=40), nullable=False, server_default="one_time"),
        sa.Column("schedule_config", sa.JSON(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])
    op.create_index("ix_alerts_status", "alerts", ["status"])
    op.create_index("ix_alerts_channel", "alerts", ["channel"])
    op.create_index("ix_alerts_next_run_at", "alerts", ["next_run_at"])

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("channel", sa.Enum("in_app", "email", "sms", "push", name="channeltype"), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "channel", name="uq_user_channel_pref"),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"])
    op.create_index("ix_user_preferences_channel", "user_preferences", ["channel"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index("ix_notifications_related_alert_id", "notifications", ["related_alert_id"])

    op.create_table(
        "notification_delivery_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.id"), nullable=True),
        sa.Column("channel", sa.Enum("in_app", "email", "sms", "push", name="channeltype"), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("provider_message_id", sa.String(length=200), nullable=True),
        sa.Column("error", sa.String(length=500), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_notification_delivery_logs_user_id", "notification_delivery_logs", ["user_id"])
    op.create_index("ix_notification_delivery_logs_alert_id", "notification_delivery_logs", ["alert_id"])
    op.create_index("ix_notification_delivery_logs_channel", "notification_delivery_logs", ["channel"])
    op.create_index("ix_notification_delivery_logs_status", "notification_delivery_logs", ["status"])
    op.create_index("ix_notification_delivery_logs_created_at", "notification_delivery_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("notification_delivery_logs")
    op.drop_table("notifications")
    op.drop_table("user_preferences")
    op.drop_table("alerts")
    op.drop_table("templates")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS channeltype")
    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
