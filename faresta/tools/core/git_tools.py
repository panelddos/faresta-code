import subprocess
from pathlib import Path
from ..base import Tool


class GitStatusTool(Tool):
    name = "git_status"
    description = "Show git status of the repository. Returns modified, staged, untracked files."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Repository path (default: current working directory)",
            }
        },
        "required": [],
    }

    def execute(self, path: str | None = None) -> str:
        cwd = Path(path).expanduser().resolve() if path else Path.cwd()
        try:
            result = subprocess.run(
                ["git", "status", "--short"],
                capture_output=True, text=True, timeout=15, cwd=str(cwd),
            )
            if result.returncode != 0:
                return f"Not a git repository or error: {result.stderr.strip()}"
            output = result.stdout.strip()
            if not output:
                result = subprocess.run(
                    ["git", "log", "--oneline", "-1"],
                    capture_output=True, text=True, timeout=15, cwd=str(cwd),
                )
                branch = subprocess.run(
                    ["git", "branch", "--show-current"],
                    capture_output=True, text=True, timeout=15, cwd=str(cwd),
                )
                branch_name = branch.stdout.strip() or "detached HEAD"
                return f"Clean working tree on branch '{branch_name}'\nLast commit: {result.stdout.strip()}"
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True, text=True, timeout=15, cwd=str(cwd),
            )
            branch_name = branch.stdout.strip() or "detached HEAD"
            return f"Branch: {branch_name}\n{output}"
        except subprocess.TimeoutExpired:
            return "Error: git status timed out"
        except FileNotFoundError:
            return "Error: git is not installed"
        except Exception as e:
            return f"Error: {e}"


class GitDiffTool(Tool):
    name = "git_diff"
    description = "Show unstaged diff of changes in the repository."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Repository path (default: current working directory)",
            },
            "staged": {
                "type": "boolean",
                "description": "Show staged diff instead of unstaged (default: false)",
            },
        },
        "required": [],
    }

    def execute(self, path: str | None = None, staged: bool = False) -> str:
        cwd = Path(path).expanduser().resolve() if path else Path.cwd()
        try:
            cmd = ["git", "diff"]
            if staged:
                cmd.append("--staged")
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=15, cwd=str(cwd),
            )
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            output = result.stdout.strip()
            if not output:
                return "No changes to show"
            if len(output) > 10000:
                output = output[:10000] + "\n... [truncated at 10000 chars]"
            return output
        except subprocess.TimeoutExpired:
            return "Error: git diff timed out"
        except FileNotFoundError:
            return "Error: git is not installed"
        except Exception as e:
            return f"Error: {e}"


class GitCommitTool(Tool):
    name = "git_commit"
    description = "Stage all changes and create a commit with a message."
    parameters = {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Commit message",
            },
            "path": {
                "type": "string",
                "description": "Repository path (default: current working directory)",
            },
        },
        "required": ["message"],
    }

    def execute(self, message: str, path: str | None = None) -> str:
        cwd = Path(path).expanduser().resolve() if path else Path.cwd()
        try:
            add = subprocess.run(
                ["git", "add", "-A"],
                capture_output=True, text=True, timeout=15, cwd=str(cwd),
            )
            if add.returncode != 0:
                return f"Error staging files: {add.stderr.strip()}"
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True, text=True, timeout=15, cwd=str(cwd),
            )
            if result.returncode != 0:
                stderr = result.stderr.strip()
                if "nothing to commit" in stderr:
                    return "Nothing to commit — working tree is clean"
                return f"Error: {stderr}"
            output = result.stdout.strip()
            return f"Committed successfully:\n{output}"
        except subprocess.TimeoutExpired:
            return "Error: git commit timed out"
        except FileNotFoundError:
            return "Error: git is not installed"
        except Exception as e:
            return f"Error: {e}"


class GitLogTool(Tool):
    name = "git_log"
    description = "Show recent commit history."
    parameters = {
        "type": "object",
        "properties": {
            "count": {
                "type": "integer",
                "description": "Number of commits to show (default: 10)",
            },
            "path": {
                "type": "string",
                "description": "Repository path (default: current working directory)",
            },
        },
        "required": [],
    }

    def execute(self, count: int = 10, path: str | None = None) -> str:
        cwd = Path(path).expanduser().resolve() if path else Path.cwd()
        try:
            result = subprocess.run(
                ["git", "log", f"--max-count={count}", "--oneline"],
                capture_output=True, text=True, timeout=15, cwd=str(cwd),
            )
            if result.returncode != 0:
                return f"Error: {result.stderr.strip()}"
            output = result.stdout.strip()
            if not output:
                return "No commits found"
            return output
        except subprocess.TimeoutExpired:
            return "Error: git log timed out"
        except FileNotFoundError:
            return "Error: git is not installed"
        except Exception as e:
            return f"Error: {e}"


class GitBranchTool(Tool):
    name = "git_branch"
    description = "List, create, or switch branches."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "create", "switch", "delete"],
                "description": "Action to perform (default: list)",
            },
            "name": {
                "type": "string",
                "description": "Branch name (required for create, switch, delete)",
            },
            "path": {
                "type": "string",
                "description": "Repository path (default: current working directory)",
            },
        },
        "required": [],
    }

    def execute(self, action: str = "list", name: str | None = None, path: str | None = None) -> str:
        cwd = Path(path).expanduser().resolve() if path else Path.cwd()
        try:
            if action == "list":
                result = subprocess.run(
                    ["git", "branch"],
                    capture_output=True, text=True, timeout=15, cwd=str(cwd),
                )
                if result.returncode != 0:
                    return f"Error: {result.stderr.strip()}"
                return result.stdout.strip() or "No branches found"
            elif action == "create":
                if not name:
                    return "Error: 'name' required for create action"
                result = subprocess.run(
                    ["git", "branch", name],
                    capture_output=True, text=True, timeout=15, cwd=str(cwd),
                )
                if result.returncode != 0:
                    return f"Error: {result.stderr.strip()}"
                return f"Created branch '{name}'"
            elif action == "switch":
                if not name:
                    return "Error: 'name' required for switch action"
                result = subprocess.run(
                    ["git", "switch", name],
                    capture_output=True, text=True, timeout=15, cwd=str(cwd),
                )
                if result.returncode != 0:
                    return f"Error: {result.stderr.strip()}"
                return f"Switched to branch '{name}'"
            elif action == "delete":
                if not name:
                    return "Error: 'name' required for delete action"
                result = subprocess.run(
                    ["git", "branch", "-d", name],
                    capture_output=True, text=True, timeout=15, cwd=str(cwd),
                )
                if result.returncode != 0:
                    return f"Error: {result.stderr.strip()}"
                return f"Deleted branch '{name}'"
            return f"Error: unknown action '{action}'"
        except subprocess.TimeoutExpired:
            return "Error: git branch operation timed out"
        except FileNotFoundError:
            return "Error: git is not installed"
        except Exception as e:
            return f"Error: {e}"