"""Report generation routes (async via Celery with sync fallback)."""
import os

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import require_roles
from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.models import User, UserRole
from app.schemas import ReportRequest, TaskStatusOut
from app.services.report_service import (
    VALID_REPORTS,
    generate_report,
    generate_report_task,
)

router = APIRouter(prefix="/api/reports", tags=["Reports"])

REPORT_ROLES = (UserRole.admin, UserRole.manager)


@router.post("", response_model=TaskStatusOut, status_code=status.HTTP_202_ACCEPTED)
def request_report(
    payload: ReportRequest,
    _: User = Depends(require_roles(*REPORT_ROLES)),
):
    if payload.report_type not in VALID_REPORTS:
        raise HTTPException(status_code=400, detail="Неизвестный тип отчёта")

    try:
        task = generate_report_task.delay(payload.report_type)
        return TaskStatusOut(task_id=task.id, status="PENDING")
    except Exception:
        # Broker unavailable -> run synchronously so the feature still works.
        filename = generate_report(payload.report_type)
        return TaskStatusOut(task_id=filename, status="SUCCESS", result=filename)


@router.get("/status/{task_id}", response_model=TaskStatusOut)
def report_status(
    task_id: str,
    _: User = Depends(require_roles(*REPORT_ROLES)),
):
    # Synchronous fallback stores filename directly as the task_id.
    if task_id.endswith(".csv"):
        return TaskStatusOut(task_id=task_id, status="SUCCESS", result=task_id)

    result = AsyncResult(task_id, app=celery_app)
    return TaskStatusOut(
        task_id=task_id,
        status=result.status,
        result=str(result.result) if result.successful() else None,
    )


@router.get("/download/{filename}")
def download_report(
    filename: str,
    _: User = Depends(require_roles(*REPORT_ROLES)),
):
    safe_name = os.path.basename(filename)
    path = os.path.join(settings.REPORTS_DIR, safe_name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Файл отчёта не найден")
    return FileResponse(path, filename=safe_name, media_type="text/csv")
