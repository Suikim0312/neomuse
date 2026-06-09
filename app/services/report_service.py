"""Asynchronous report generation via Celery (with synchronous fallback).

Reports are written as CSV files into the configured reports directory.
If Celery/Redis are not available the task can still be executed inline
through ``generate_report`` so the feature degrades gracefully.
"""
import csv
import logging
import os
from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import Excursion, Ticket, User, UserRole

logger = logging.getLogger(__name__)

VALID_REPORTS = {"ticket_sales", "visitor_stats", "excursion_schedule"}


def _ensure_reports_dir() -> str:
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    return settings.REPORTS_DIR


def _write_csv(filename: str, header: list[str], rows: list[list]) -> str:
    reports_dir = _ensure_reports_dir()
    path = os.path.join(reports_dir, filename)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)
    return filename


def generate_report(report_type: str) -> str:
    """Generate a report file and return its filename. Runs synchronously."""
    if report_type not in VALID_REPORTS:
        raise ValueError(f"Unknown report type: {report_type}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    db = SessionLocal()
    try:
        if report_type == "ticket_sales":
            rows = [
                [t.id, t.visitor_id, t.ticket_type.value, t.visit_date,
                 t.price, t.status.value, t.created_at]
                for t in db.query(Ticket).all()
            ]
            return _write_csv(
                f"ticket_sales_{timestamp}.csv",
                ["id", "visitor_id", "type", "visit_date", "price",
                 "status", "created_at"],
                rows,
            )

        if report_type == "visitor_stats":
            rows = [
                [u.id, u.full_name, u.email, u.role.value, u.is_active, u.created_at]
                for u in db.query(User).filter(User.role == UserRole.visitor).all()
            ]
            return _write_csv(
                f"visitor_stats_{timestamp}.csv",
                ["id", "full_name", "email", "role", "is_active", "created_at"],
                rows,
            )

        # excursion_schedule
        rows = [
            [e.id, e.title, e.guide_id, e.start_time, e.end_time,
             e.max_participants, e.status.value]
            for e in db.query(Excursion).all()
        ]
        return _write_csv(
            f"excursion_schedule_{timestamp}.csv",
            ["id", "title", "guide_id", "start_time", "end_time",
             "max_participants", "status"],
            rows,
        )
    finally:
        db.close()


@celery_app.task(name="app.services.report_service.generate_report_task")
def generate_report_task(report_type: str) -> str:
    """Celery task wrapper around :func:`generate_report`."""
    logger.info("Generating report: %s", report_type)
    return generate_report(report_type)
