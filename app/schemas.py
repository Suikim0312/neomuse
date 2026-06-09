"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# NOTE: emails are stored/validated as plain strings rather than EmailStr
# because the project uses internal ``*.local`` addresses, which the strict
# email-validator rejects as special-use domains.
EmailStr = str

from app.db.models import (
    BookingStatus,
    ExcursionStatus,
    TicketStatus,
    TicketType,
    UserRole,
)


# ---------- Auth / Users ----------
class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.visitor


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Exhibits ----------
class ExhibitBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    category: str = ""
    origin: str = ""
    period: str = ""
    condition_status: str = ""
    location_hall: str = ""
    image_url: str = ""
    is_available: bool = True


class ExhibitCreate(ExhibitBase):
    pass


class ExhibitUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    origin: Optional[str] = None
    period: Optional[str] = None
    condition_status: Optional[str] = None
    location_hall: Optional[str] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None


class ExhibitOut(ExhibitBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


# ---------- Tickets ----------
class TicketCreate(BaseModel):
    ticket_type: TicketType
    visit_date: datetime


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    visitor_id: int
    ticket_type: TicketType
    visit_date: datetime
    price: float
    status: TicketStatus
    qr_code: str
    created_at: datetime


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


# ---------- Excursions ----------
class ExcursionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    guide_id: Optional[int] = None
    start_time: datetime
    end_time: datetime
    max_participants: int = Field(default=10, ge=1)


class ExcursionUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    guide_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_participants: Optional[int] = None
    status: Optional[ExcursionStatus] = None


class ExcursionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    guide_id: Optional[int]
    start_time: datetime
    end_time: datetime
    max_participants: int
    status: ExcursionStatus
    created_at: datetime


class ExcursionBookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    excursion_id: int
    visitor_id: int
    booking_status: BookingStatus
    created_at: datetime


# ---------- Reports ----------
class ReportRequest(BaseModel):
    report_type: str = Field(description="ticket_sales | visitor_stats | excursion_schedule")


class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
