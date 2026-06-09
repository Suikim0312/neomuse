"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-01-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role = sa.Enum("admin", "manager", "guide", "visitor", name="userrole")
ticket_type = sa.Enum("adult", "student", "child", "group", name="tickettype")
ticket_status = sa.Enum("booked", "paid", "cancelled", "used", name="ticketstatus")
excursion_status = sa.Enum(
    "scheduled", "in_progress", "completed", "cancelled", name="excursionstatus"
)
booking_status = sa.Enum(
    "registered", "cancelled", "attended", name="bookingstatus"
)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "exhibits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("category", sa.String(120)),
        sa.Column("origin", sa.String(120)),
        sa.Column("period", sa.String(120)),
        sa.Column("condition_status", sa.String(120)),
        sa.Column("location_hall", sa.String(120)),
        sa.Column("image_url", sa.String(500)),
        sa.Column("is_available", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_index("ix_exhibits_title", "exhibits", ["title"])
    op.create_index("ix_exhibits_category", "exhibits", ["category"])

    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("visitor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("ticket_type", ticket_type, nullable=False),
        sa.Column("visit_date", sa.DateTime(), nullable=False),
        sa.Column("price", sa.Float()),
        sa.Column("status", ticket_status),
        sa.Column("qr_code", sa.String(255)),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_tickets_visit_date", "tickets", ["visit_date"])
    op.create_index("ix_tickets_status", "tickets", ["status"])

    op.create_table(
        "excursions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("guide_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=False),
        sa.Column("max_participants", sa.Integer()),
        sa.Column("status", excursion_status),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_index("ix_excursions_start_time", "excursions", ["start_time"])

    op.create_table(
        "excursion_bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("excursion_id", sa.Integer(), sa.ForeignKey("excursions.id"), nullable=False),
        sa.Column("visitor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("booking_status", booking_status),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("excursion_bookings")
    op.drop_index("ix_excursions_start_time", table_name="excursions")
    op.drop_table("excursions")
    op.drop_index("ix_tickets_status", table_name="tickets")
    op.drop_index("ix_tickets_visit_date", table_name="tickets")
    op.drop_table("tickets")
    op.drop_index("ix_exhibits_category", table_name="exhibits")
    op.drop_index("ix_exhibits_title", table_name="exhibits")
    op.drop_table("exhibits")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
