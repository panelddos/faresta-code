from ..registry import register_tool
from .twitter import TwitterTool
from .telegram import TelegramTool
from .discord import DiscordTool


def register_social_tools():
    for tool in [
        TwitterTool(),
        TelegramTool(),
        DiscordTool(),
    ]:
        register_tool(tool)
