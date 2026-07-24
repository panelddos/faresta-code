import os
import httpx
from ..base import Tool


class TelegramTool(Tool):
    name = "telegram"
    description = "Send messages via Telegram bot. Requires TELEGRAM_BOT_TOKEN env var."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["send"],
                "description": "Action: 'send' to send a message",
            },
            "chat_id": {
                "type": "string",
                "description": "Telegram chat/group/channel ID (e.g. '-1001234567890')",
            },
            "text": {
                "type": "string",
                "description": "Message text to send",
            },
        },
        "required": ["action", "chat_id", "text"],
    }

    def execute(self, action: str, chat_id: str = "", text: str = "") -> str:
        if action == "send":
            return self._send_message(chat_id, text)
        return f"Unknown action: {action}"

    def _send_message(self, chat_id: str, text: str) -> str:
        if not chat_id or not text:
            return "Error: chat_id and text are required"
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not bot_token:
            return "Error: TELEGRAM_BOT_TOKEN not set"

        try:
            with httpx.Client() as client:
                resp = client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    msg_id = data.get("result", {}).get("message_id", "unknown")
                    return f"Message sent to {chat_id}! Message ID: {msg_id}"
                return f"Error sending message: {resp.status_code} - {resp.text}"
        except Exception as e:
            return f"Error sending message: {e}"
