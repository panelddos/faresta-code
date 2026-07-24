import os
import httpx
from ..base import Tool


class DiscordTool(Tool):
    name = "discord"
    description = "Send messages to Discord channels via webhook. Requires DISCORD_WEBHOOK_URL env var or pass webhook_url."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["send"],
                "description": "Action: 'send' to send a message",
            },
            "text": {
                "type": "string",
                "description": "Message content to send",
            },
            "webhook_url": {
                "type": "string",
                "description": "Discord webhook URL (optional if DISCORD_WEBHOOK_URL env var is set)",
            },
        },
        "required": ["action", "text"],
    }

    def execute(self, action: str, text: str = "", webhook_url: str = "") -> str:
        if action == "send":
            return self._send_message(text, webhook_url)
        return f"Unknown action: {action}"

    def _send_message(self, text: str, webhook_url: str = "") -> str:
        if not text:
            return "Error: text is required"

        url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL", "")
        if not url:
            return "Error: no webhook URL. Set DISCORD_WEBHOOK_URL env var or pass webhook_url parameter."

        try:
            with httpx.Client() as client:
                resp = client.post(url, json={"content": text})
                if resp.status_code in (200, 204):
                    return "Message sent to Discord successfully!"
                return f"Error sending to Discord: {resp.status_code} - {resp.text}"
        except Exception as e:
            return f"Error sending to Discord: {e}"
