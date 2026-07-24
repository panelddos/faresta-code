import os
import subprocess
from pathlib import Path
from ..base import Tool


class ReadFileTool(Tool):
    name = "read"
    description = "Read the contents of a file. Returns the full file content."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to read",
            }
        },
        "required": ["file_path"],
    }

    def execute(self, file_path: str) -> str:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"Error: file not found: {file_path}"
        if not path.is_file():
            return f"Error: not a file: {file_path}"
        try:
            content = path.read_text(encoding="utf-8")
            if len(content) > 50000:
                content = content[:50000] + "\n... [truncated at 50000 chars]"
            return content
        except Exception as e:
            return f"Error reading {file_path}: {e}"


class WriteFileTool(Tool):
    name = "write"
    description = "Write content to a file. Creates parent directories if needed. Overwrites existing files."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        },
        "required": ["file_path", "content"],
    }

    def execute(self, file_path: str, content: str) -> str:
        path = Path(file_path).expanduser().resolve()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} bytes to {file_path}"
        except Exception as e:
            return f"Error writing to {file_path}: {e}"


class EditFileTool(Tool):
    name = "edit"
    description = "Find and replace text in a file. Use this to make targeted changes."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file to edit",
            },
            "old_string": {
                "type": "string",
                "description": "Text to find (must be unique in file)",
            },
            "new_string": {
                "type": "string",
                "description": "Text to replace with",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    }

    def execute(self, file_path: str, old_string: str, new_string: str) -> str:
        path = Path(file_path).expanduser().resolve()
        if not path.exists():
            return f"Error: file not found: {file_path}"
        try:
            content = path.read_text(encoding="utf-8")
            count = content.count(old_string)
            if count == 0:
                return f"Error: string not found in {file_path}"
            content = content.replace(old_string, new_string, 1)
            path.write_text(content, encoding="utf-8")
            return f"Successfully replaced in {file_path}"
        except Exception as e:
            return f"Error editing {file_path}: {e}"


class GlobTool(Tool):
    name = "glob"
    description = "Search for files matching a glob pattern. Returns matching file paths."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Glob pattern (e.g. '**/*.py', 'src/**/*.ts')",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current working directory)",
            },
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str, path: str | None = None) -> str:
        search_dir = Path(path).expanduser().resolve() if path else Path.cwd()
        try:
            matches = [str(p.relative_to(search_dir)) for p in search_dir.rglob(pattern) if p.is_file()]
            if not matches:
                return f"No files matching '{pattern}' found in {search_dir}"
            result = "\n".join(sorted(matches)[:200])
            if len(matches) > 200:
                result += f"\n... and {len(matches) - 200} more"
            return result
        except Exception as e:
            return f"Error globbing: {e}"


class GrepTool(Tool):
    name = "grep"
    description = "Search file contents using a regex pattern. Returns matching lines with file paths and line numbers."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {
                "type": "string",
                "description": "Regex pattern to search for",
            },
            "include": {
                "type": "string",
                "description": "File glob pattern to include (e.g. '*.py', '*.{ts,tsx}')",
            },
            "path": {
                "type": "string",
                "description": "Directory to search in (default: current working directory)",
            },
        },
        "required": ["pattern"],
    }

    def execute(self, pattern: str, include: str | None = None, path: str | None = None) -> str:
        search_dir = Path(path).expanduser().resolve() if path else Path.cwd()
        try:
            cmd = ["rg", "-n", pattern, str(search_dir)]
            if include:
                cmd.extend(["--include", include])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                output = result.stdout.strip()
                if not output:
                    return f"No matches for '{pattern}'"
                lines = output.split("\n")
                if len(lines) > 200:
                    lines = lines[:200] + [f"... and {len(lines) - 200} more"]
                return "\n".join(lines)
            elif result.returncode == 1:
                return f"No matches for '{pattern}'"
            else:
                return f"Error searching: {result.stderr.strip()}"
        except FileNotFoundError:
            return "Error: ripgrep (rg) is not installed. Install it with: apt install ripgrep"
        except subprocess.TimeoutExpired:
            return f"Error: search timed out after 30s"
        except Exception as e:
            return f"Error searching: {e}"


class LsTool(Tool):
    name = "ls"
    description = "List files and directories in a path. Shows names, types, and sizes."
    parameters = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list (default: current working directory)",
            },
        },
        "required": [],
    }

    def execute(self, path: str | None = None) -> str:
        target = Path(path).expanduser().resolve() if path else Path.cwd()
        if not target.exists():
            return f"Error: path not found: {path}"
        if not target.is_dir():
            return f"Error: not a directory: {path}"
        try:
            entries = []
            for p in sorted(target.iterdir()):
                suffix = "/" if p.is_dir() else ""
                size = p.stat().st_size if p.is_file() else 0
                size_str = f" ({size} bytes)" if size else ""
                entries.append(f"{p.name}{suffix}{size_str}")
            return "\n".join(entries) if entries else "(empty directory)"
        except Exception as e:
            return f"Error listing {path}: {e}"