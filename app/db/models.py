"""SQLAlchemy ORM models for NeoMuse."""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    guide = "guide"
    visitor = "visitor"


class TicketType(str, enum.Enum):
    adult = "adult"
    student = "student"
    child = "child"
    group = "group"


class TicketStatus(str, enum.Enum):
    booked = "booked"
    paid = "paid"
    cancelled = "cancelled"
    used = "used"


class ExcursionStatus(str, enum.Enum):
    scheduled = "scheduled"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class BookingStatus(str, enum.Enum):
    registered = "registered"
    cancelled = "cancelled"
    attended = "attended"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.visitor, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="visitor", cascade="all, delete-orphan"
    )
    guided_excursions: Mapped[list["Excursion"]] = relationship(
        back_populates="guide", foreign_keys="Excursion.guide_id"
    )
    excursion_bookings: Mapped[list["ExcursionBooking"]] = relationship(
        back_populates="visitor", cascade="all, delete-orphan"
    )


class Exhibit(Base):
    __tablename__ = "exhibits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(120), index=True, default="")
    origin: Mapped[str] = mapped_column(String(120), default="")
    period: Mapped[str] = mapped_column(String(120), default="")
    condition_status: Mapped[str] = mapped_column(String(120), default="")
    location_hall: Mapped[str] = mapped_column(String(120), default="")
    image_url: Mapped[str] = mapped_column(String(500), default="")
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )
    # i18n translation columns
    title_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title_kz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_kz: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_en: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category_kz: Mapped[str | None] = mapped_column(String(120), nullable=True)
    period_en: Mapped[str | None] = mapped_column(String(120), nullable=True)
    period_kz: Mapped[str | None] = mapped_column(String(120), nullable=True)
    history: Mapped[str | None] = mapped_column(Text, nullable=True)
    significance: Mapped[str | None] = mapped_column(Text, nullable=True)
    interesting_facts: Mapped[str | None] = mapped_column(Text, nullable=True)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    visitor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    ticket_type: Mapped[TicketType] = mapped_column(Enum(TicketType), nullable=False)
    visit_date: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus), default=TicketStatus.booked, index=True
    )
    qr_code: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    visitor: Mapped["User"] = relationship(back_populates="tickets")


class Excursion(Base):
    __tablename__ = "excursions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    guide_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # i18n translation columns
    title_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title_kz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_kz: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_time: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, default=10)
    status: Mapped[ExcursionStatus] = mapped_column(
        Enum(ExcursionStatus), default=ExcursionStatus.scheduled
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    guide: Mapped["User"] = relationship(
        back_populates="guided_excursions", foreign_keys=[guide_id]
    )
    bookings: Mapped[list["ExcursionBooking"]] = relationship(
        back_populates="excursion", cascade="all, delete-orphan"
    )


class ExcursionBooking(Base):
    __tablename__ = "excursion_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    excursion_id: Mapped[int] = mapped_column(
        ForeignKey("excursions.id"), nullable=False
    )
    visitor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    booking_status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus), default=BookingStatus.registered
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    excursion: Mapped["Excursion"] = relationship(back_populates="bookings")
    visitor: Mapped["User"] = relationship(back_populates="excursion_bookings")
