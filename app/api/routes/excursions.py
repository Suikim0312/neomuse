"""Excursion scheduling and booking routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.database import get_db
from app.db.models import (
    BookingStatus,
    Excursion,
    ExcursionBooking,
    User,
    UserRole,
)
from app.schemas import (
    ExcursionBookingOut,
    ExcursionCreate,
    ExcursionOut,
    ExcursionUpdate,
)
from app.services.cache_service import invalidate_dashboard

router = APIRouter(prefix="/api/excursions", tags=["Excursions"])

PLANNERS = (UserRole.admin, UserRole.manager)


def _notify_excursion(excursion: Excursion) -> None:
    from app.services.telegram_service import send_notification

    send_notification(
        f"🗓 Создана экскурсия «{excursion.title}» на "
        f"{excursion.start_time:%d.%m.%Y %H:%M}"
    )


@router.get("", response_model=list[ExcursionOut])
def list_excursions(db: Session = Depends(get_db)):
    return db.query(Excursion).order_by(Excursion.start_time.asc()).all()


@router.get("/assigned", response_model=list[ExcursionOut])
def assigned_excursions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.guide)),
):
    return (
        db.query(Excursion)
        .filter(Excursion.guide_id == current_user.id)
        .order_by(Excursion.start_time.asc())
        .all()
    )


@router.get("/{excursion_id}", response_model=ExcursionOut)
def get_excursion(excursion_id: int, db: Session = Depends(get_db)):
    excursion = db.get(Excursion, excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена")
    return excursion


@router.get("/{excursion_id}/participants", response_model=list[ExcursionBookingOut])
def participants(
    excursion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    excursion = db.get(Excursion, excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена")
    is_guide = current_user.id == excursion.guide_id
    if current_user.role not in PLANNERS and not is_guide:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return (
        db.query(ExcursionBooking)
        .filter(ExcursionBooking.excursion_id == excursion_id)
        .all()
    )


@router.post("", response_model=ExcursionOut, status_code=status.HTTP_201_CREATED)
def create_excursion(
    payload: ExcursionCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*PLANNERS)),
):
    if payload.end_time <= payload.start_time:
        raise HTTPException(
            status_code=400, detail="Время окончания должно быть позже начала"
        )
    excursion = Excursion(**payload.model_dump())
    db.add(excursion)
    db.commit()
    db.refresh(excursion)
    invalidate_dashboard()
    _notify_excursion(excursion)
    return excursion


@router.put("/{excursion_id}", response_model=ExcursionOut)
def update_excursion(
    excursion_id: int,
    payload: ExcursionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    excursion = db.get(Excursion, excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена")

    data = payload.model_dump(exclude_unset=True)
    is_guide = current_user.id == excursion.guide_id

    # Guides may only update the status of their own excursions.
    if current_user.role == UserRole.guide:
        if not is_guide or set(data.keys()) - {"status"}:
            raise HTTPException(
                status_code=403, detail="Гид может изменять только статус"
            )
    elif current_user.role not in PLANNERS:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    for field, value in data.items():
        setattr(excursion, field, value)
    db.commit()
    db.refresh(excursion)
    invalidate_dashboard()
    return excursion


@router.post(
    "/{excursion_id}/register",
    response_model=ExcursionBookingOut,
    status_code=status.HTTP_201_CREATED,
)
def register_for_excursion(
    excursion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    excursion = db.get(Excursion, excursion_id)
    if not excursion:
        raise HTTPException(status_code=404, detail="Экскурсия не найдена")

    existing = (
        db.query(ExcursionBooking)
        .filter(
            ExcursionBooking.excursion_id == excursion_id,
            ExcursionBooking.visitor_id == current_user.id,
            ExcursionBooking.booking_status == BookingStatus.registered,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже записаны на эту экскурсию")

    count = (
        db.query(func.count(ExcursionBooking.id))
        .filter(
            ExcursionBooking.excursion_id == excursion_id,
            ExcursionBooking.booking_status == BookingStatus.registered,
        )
        .scalar()
        or 0
    )
    if count >= excursion.max_participants:
        raise HTTPException(status_code=400, detail="Свободных мест больше нет")

    booking = ExcursionBooking(
        excursion_id=excursion_id, visitor_id=current_user.id
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/bookings/my", response_model=list[ExcursionBookingOut])
def my_excursion_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ExcursionBooking)
        .filter(ExcursionBooking.visitor_id == current_user.id)
        .all()
    )
