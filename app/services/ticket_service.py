"""Ticket business logic: price calculation and QR code generation."""
import uuid

from app.db.models import TicketType

# Base prices in local currency (KZT) per ticket type.
TICKET_PRICES: dict[TicketType, float] = {
    TicketType.adult: 3000.0,
    TicketType.student: 1500.0,
    TicketType.child: 1000.0,
    TicketType.group: 12000.0,
}


def calculate_price(ticket_type: TicketType) -> float:
    return TICKET_PRICES.get(ticket_type, TICKET_PRICES[TicketType.adult])


def generate_qr_code(ticket_type: TicketType) -> str:
    """Generate a simple unique QR payload string (placeholder content)."""
    return f"NEOMUSE-{ticket_type.value.upper()}-{uuid.uuid4().hex[:12]}"
