"""Ticket booking routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.db.models import Ticket, TicketStatus, User, UserRole
from app.schemas import TicketCreate, TicketOut, TicketStatusUpdate
from app.services.cache_service import invalidate_dashboard
from app.services.ticket_service import calculate_price, generate_qr_code

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])

STAFF = (UserRole.admin, UserRole.manager)


def _notify_ticket(ticket: Ticket) -> None:
    """Trigger a Telegram notification in the background (best effort)."""
    from app.services.telegram_service import send_notification

    send_notification(
        f"🎟 Забронирован билет #{ticket.id} ({ticket.ticket_type.value}) "
        f"на {ticket.visit_date:%d.%m.%Y}. Сумма: {ticket.price:.0f} ₸"
    )


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def book_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = Ticket(
        visitor_id=current_user.id,
        ticket_type=payload.ticket_type,
        visit_date=payload.visit_date,
        price=calculate_price(payload.ticket_type),
        status=TicketStatus.booked,
        qr_code=generate_qr_code(payload.ticket_type),
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    invalidate_dashboard()
    _notify_ticket(ticket)
    return ticket


@router.get("/my", response_model=list[TicketOut])
def my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Ticket)
        .filter(Ticket.visitor_id == current_user.id)
        .order_by(Ticket.created_at.desc())
        .all()
    )


@router.get("", response_model=list[TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*STAFF)),
):
    return db.query(Ticket).order_by(Ticket.created_at.desc()).all()


@router.put("/{ticket_id}/status", response_model=TicketOut)
def update_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*STAFF)),
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Билет не найден")
    ticket.status = payload.status
    db.commit()
    db.refresh(ticket)
    invalidate_dashboard()
    return ticket


@router.post("/{ticket_id}/cancel", response_model=TicketOut)
def cancel_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Билет не найден")
    if ticket.visitor_id != current_user.id and current_user.role not in STAFF:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    ticket.status = TicketStatus.cancelled
    db.commit()
    db.refresh(ticket)
    invalidate_dashboard()
    return ticket
