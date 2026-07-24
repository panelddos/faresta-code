from ..registry import register_tool
from .file_ops import ReadFileTool, WriteFileTool, EditFileTool, GlobTool, GrepTool, LsTool
from .bash import BashTool
from .web import WebFetchTool, WebSearchTool


def register_core_tools():
    for tool in [
        ReadFileTool(), WriteFileTool(), EditFileTool(),
        GlobTool(), GrepTool(), LsTool(),
        BashTool(),
        WebFetchTool(), WebSearchTool(),
    ]:
        register_tool(tool)
