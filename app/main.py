"""NeoMuse FastAPI application entry point."""
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import (
    analytics,
    auth,
    excursions,
    exhibits,
    reports,
    tickets,
    users,
    webhooks,
)
from app.core.config import settings
from app.db.init_db import init_db
from app.web import router as web_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

tags_metadata = [
    {"name": "Auth", "description": "Регистрация, вход и текущий пользователь"},
    {"name": "Users", "description": "Управление пользователями (Admin)"},
    {"name": "Exhibits", "description": "Каталог экспонатов"},
    {"name": "Tickets", "description": "Билеты и бронирование"},
    {"name": "Excursions", "description": "Планирование экскурсий"},
    {"name": "Analytics", "description": "Аналитика и статистика"},
    {"name": "Reports", "description": "Генерация отчётов"},
    {"name": "Webhooks", "description": "Webhook-эндпоинты Telegram"},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Современная платформа управления музеем NeoMuse.",
    version="1.0.0",
    openapi_tags=tags_metadata,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# REST API routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(exhibits.router)
app.include_router(tickets.router)
app.include_router(excursions.router)
app.include_router(analytics.router)
app.include_router(reports.router)
app.include_router(webhooks.router)

# Server-rendered HTML UI
app.include_router(web_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    logger.info("NeoMuse запущен.")


@app.get("/health", tags=["Analytics"])
def health() -> dict:
    return {"status": "ok"}
