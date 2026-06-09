"""Analytics dashboard API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.database import get_db
from app.db.models import User, UserRole
from app.services.analytics_service import get_dashboard_stats

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

VIEWERS = (UserRole.admin, UserRole.manager)


@router.get("/dashboard")
def dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(*VIEWERS)),
):
    return get_dashboard_stats(db)
