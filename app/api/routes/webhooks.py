"""Telegram webhook handling."""
import logging

from fastapi import APIRouter, Request

from app.services.telegram_service import validate_update

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """Accept incoming Telegram updates, validate and log them safely."""
    try:
        payload = await request.json()
    except Exception:
        logger.warning("Telegram webhook received invalid JSON")
        return {"ok": False, "error": "invalid payload"}

    if not validate_update(payload):
        logger.warning("Telegram webhook received malformed update")
        return {"ok": False, "error": "invalid update structure"}

    message = payload.get("message", {})
    text = message.get("text", "")
    chat = message.get("chat", {}).get("id")
    logger.info("Telegram update %s: chat=%s text=%s",
                payload.get("update_id"), chat, text)

    return {"ok": True}
