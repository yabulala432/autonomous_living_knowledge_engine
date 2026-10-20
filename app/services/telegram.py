import httpx
from typing import Optional
from app.core.config import settings

async def send_telegram_alert(text: str, chat_id: Optional[str] = None) -> bool:
    """
    Sends an alert message to a designated Telegram chat or group.
    Uses settings.telegram_bot_token and settings.telegram_chat_id by default.
    """
    token = settings.telegram_bot_token
    target_chat = chat_id or settings.telegram_chat_id

    if not token or not target_chat:
        print("[Telegram Service] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured. Skipping alert.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                print(f"[Telegram Service] Alert sent successfully to chat {target_chat}")
                return True
            else:
                print(f"[Telegram Service] Failed to send message: {response.status_code} - {response.text}")
                return False
    except Exception as e:
        print(f"[Telegram Service] Error communicating with Telegram API: {e}")
        return False
