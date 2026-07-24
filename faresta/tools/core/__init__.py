from ..registry import register_tool
from .file_ops import ReadFileTool, WriteFileTool, EditFileTool, GlobTool, GrepTool, LsTool
from .bash import BashTool
from .web import WebFetchTool, WebSearchTool
from .git_tools import GitStatusTool, GitDiffTool, GitCommitTool, GitLogTool, GitBranchTool
from .lint_tools import LintTestTool


def register_core_tools():
    for tool in [
        ReadFileTool(), WriteFileTool(), EditFileTool(),
        GlobTool(), GrepTool(), LsTool(),
        BashTool(),
        WebFetchTool(), WebSearchTool(),
        GitStatusTool(), GitDiffTool(), GitCommitTool(), GitLogTool(), GitBranchTool(),
        LintTestTool(),
    ]:
        register_tool(tool)