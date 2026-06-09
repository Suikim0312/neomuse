"""Analytics computations with Redis caching.

Uses aggregate SQL queries to keep the dashboard responsive and caches
the resulting payload for a short period.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache import cache
from app.db.models import (
    Excursion,
    ExcursionStatus,
    Ticket,
    TicketStatus,
    User,
    UserRole,
)
from app.services.cache_service import DASHBOARD_STATS_KEY, DASHBOARD_TTL


def get_dashboard_stats(db: Session) -> dict:
    cached = cache.get_json(DASHBOARD_STATS_KEY)
    if cached:
        cached["cached"] = True
        return cached

    total_visitors = (
        db.query(func.count(User.id))
        .filter(User.role == UserRole.visitor)
        .scalar()
        or 0
    )
    active_users = (
        db.query(func.count(User.id)).filter(User.is_active.is_(True)).scalar() or 0
    )
    total_tickets = db.query(func.count(Ticket.id)).scalar() or 0

    tickets_by_status = {
        status.value: 0 for status in TicketStatus
    }
    for status_value, count in (
        db.query(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status).all()
    ):
        key = status_value.value if hasattr(status_value, "value") else str(status_value)
        tickets_by_status[key] = count

    revenue = (
        db.query(func.coalesce(func.sum(Ticket.price), 0.0))
        .filter(Ticket.status.in_([TicketStatus.paid, TicketStatus.used]))
        .scalar()
        or 0.0
    )

    # Bookings per day for the last 7 days
    since = datetime.now(timezone.utc) - timedelta(days=7)
    bookings_rows = (
        db.query(func.date(Ticket.created_at), func.count(Ticket.id))
        .filter(Ticket.created_at >= since)
        .group_by(func.date(Ticket.created_at))
        .all()
    )
    bookings_per_day = [
        {"date": str(day), "count": count} for day, count in bookings_rows
    ]

    # Upcoming excursions
    upcoming = (
        db.query(Excursion)
        .filter(
            Excursion.start_time >= datetime.now(timezone.utc),
            Excursion.status == ExcursionStatus.scheduled,
        )
        .order_by(Excursion.start_time.asc())
        .limit(5)
        .all()
    )
    upcoming_excursions = [
        {"id": e.id, "title": e.title, "start_time": e.start_time.isoformat()}
        for e in upcoming
    ]

    stats = {
        "total_visitors": total_visitors,
        "active_users": active_users,
        "total_tickets": total_tickets,
        "tickets_by_status": tickets_by_status,
        "revenue": round(float(revenue), 2),
        "bookings_per_day": bookings_per_day,
        "upcoming_excursions": upcoming_excursions,
        "cached": False,
    }
    cache.set_json(DASHBOARD_STATS_KEY, stats, ttl=DASHBOARD_TTL)
    return stats
