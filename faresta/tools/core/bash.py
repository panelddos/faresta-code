import subprocess
import shlex
from pathlib import Path
from ..base import Tool


class BashTool(Tool):
    name = "bash"
    description = "Execute a shell command. Use this to run terminal commands, scripts, git operations, etc. Returns stdout and stderr."
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "Shell command to execute",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in milliseconds (default: 120000)",
            },
            "workdir": {
                "type": "string",
                "description": "Working directory for the command (default: current dir)",
            },
        },
        "required": ["command"],
    }

    def execute(self, command: str, timeout: int = 120000, workdir: str | None = None) -> str:
        cwd = Path(workdir).expanduser().resolve() if workdir else Path.cwd()
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout / 1000,
                cwd=str(cwd),
            )
            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                if output:
                    output += "\n--- stderr ---\n"
                output += result.stderr
            if result.returncode != 0 and not output:
                output = f"Command exited with code {result.returncode}"
            if not output:
                output = f"Command completed (exit code 0, no output)"
            return output.strip()
        except subprocess.TimeoutExpired:
            return f"Error: command timed out after {timeout}ms"
        except Exception as e:
            return f"Error executing command: {e}"