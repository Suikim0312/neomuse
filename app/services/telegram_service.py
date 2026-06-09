"""Telegram Bot API integration.

If TELEGRAM_BOT_TOKEN is not configured the service runs in *mock mode*:
it logs the notification instead of sending it and never crashes the app.
"""
import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def send_notification(text: str, chat_id: str | None = None) -> bool:
    """Send a Telegram message. Returns True on success, False otherwise.

    In mock mode (missing token) the message is logged and True is returned
    so that callers don't treat the missing integration as a failure.
    """
    token = settings.TELEGRAM_BOT_TOKEN
    target_chat = chat_id or settings.TELEGRAM_CHAT_ID

    if not token or not target_chat:
        logger.info("[TELEGRAM MOCK] %s", text)
        return True

    try:
        response = httpx.post(
            TELEGRAM_API_URL.format(token=token),
            json={"chat_id": target_chat, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as exc:  # broad catch: integration must never crash app
        logger.error("Telegram send failed: %s", exc)
        return False


def validate_update(payload: dict) -> bool:
    """Basic structural validation of an incoming Telegram update."""
    if not isinstance(payload, dict):
        return False
    return "update_id" in payload
