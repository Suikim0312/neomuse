"""Exhibit catalog routes with search, filtering and Redis caching."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.cache import cache
from app.db.database import get_db
from app.db.models import Exhibit, User, UserRole
from app.schemas import ExhibitCreate, ExhibitOut, ExhibitUpdate
from app.services.cache_service import (
    POPULAR_EXHIBITS_KEY,
    POPULAR_EXHIBITS_TTL,
    invalidate_exhibits,
)

router = APIRouter(prefix="/api/exhibits", tags=["Exhibits"])

EDITORS = (UserRole.admin, UserRole.manager)


@router.get("", response_model=list[ExhibitOut])
def list_exhibits(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(None, description="Search by title"),
    category: Optional[str] = None,
    period: Optional[str] = None,
    hall: Optional[str] = None,
):
    query = db.query(Exhibit)
    if search:
        query = query.filter(Exhibit.title.ilike(f"%{search}%"))
    if category:
        query = query.filter(Exhibit.category == category)
    if period:
        query = query.filter(Exhibit.period == period)
    if hall:
        query = query.filter(Exhibit.location_hall == hall)
    return query.order_by(Exhibit.created_at.desc()).all()


@router.get("/popular", response_model=list[ExhibitOut])
def popular_exhibits(db: Session = Depends(get_db)):
    """Return available exhibits, cached in Redis."""
    cached = cache.get_json(POPULAR_EXHIBITS_KEY)
    if cached is not None:
        return cached

    exhibits = (
        db.query(Exhibit)
        .filter(Exhibit.is_available.is_(True))
        .order_by(Exhibit.created_at.desc())
        .limit(10)
        .all()
    )
    data = [ExhibitOut.model_validate(e).model_dump() for e in exhibits]
    cache.set_json(POPULAR_EXHIBITS_KEY, data, ttl=POPULAR_EXHIBITS_TTL)
    return data


@router.get("/{exhibit_id}", response_model=ExhibitOut)
def get_exhibit(exhibit_id: int, db: Session = Depends(get_db)):
    exhibit = db.get(Exhibit, exhibit_id)
    if not exhibit:
        raise HTTPException(status_code=404, detail="Экспонат не найден")
    return exhibit


@router.post("", response_model=ExhibitOut, status_code=status.HTTP_201_CREATED)
def create_exhibit(
    payload: ExhibitCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*EDITORS)),
):
    exhibit = Exhibit(**payload.model_dump())
    db.add(exhibit)
    db.commit()
    db.refresh(exhibit)
    invalidate_exhibits()
    return exhibit


@router.put("/{exhibit_id}", response_model=ExhibitOut)
def update_exhibit(
    exhibit_id: int,
    payload: ExhibitUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*EDITORS)),
):
    exhibit = db.get(Exhibit, exhibit_id)
    if not exhibit:
        raise HTTPException(status_code=404, detail="Экспонат не найден")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exhibit, field, value)
    db.commit()
    db.refresh(exhibit)
    invalidate_exhibits()
    return exhibit


@router.delete("/{exhibit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exhibit(
    exhibit_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*EDITORS)),
):
    exhibit = db.get(Exhibit, exhibit_id)
    if not exhibit:
        raise HTTPException(status_code=404, detail="Экспонат не найден")
    db.delete(exhibit)
    db.commit()
    invalidate_exhibits()
