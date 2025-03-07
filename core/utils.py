import logging
import os

import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
TELEGRAM_DEBUG = os.getenv("TELEGRAM_DEBUG", "False").lower() in ("true", "1", "yes")

logger = logging.getLogger(__name__)

if TELEGRAM_DEBUG and (not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL):
    raise EnvironmentError("For debugging via Telegram, TELEGRAM_BOT_TOKEN and TELEGRAM_CHANNEL must be set.")


def send_debug_telegram(message: str) -> None:
    """
    Sends a debug message to the Telegram channel.
    The message is sent only if TELEGRAM_DEBUG is enabled.
    """
    if not TELEGRAM_DEBUG:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    params = {"chat_id": f"@{TELEGRAM_CHANNEL}", "text": message}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code != 200:
            logger.error(f"Error sending to Telegram, status: {response.status_code}, response: {response.text}")
    except Exception as e:
        logger.error(f"Error sending message to Telegram: {e}")