import os
import json
from pathlib import Path
from pydantic import BaseModel

FARESTA_JSON_NAME = "faresta.json"


class ProjectPermissions(BaseModel):
    allow: list[str] = []
    deny: list[str] = []
    ask: list[str] = []


class ProjectConfig(BaseModel):
    permissions: ProjectPermissions = ProjectPermissions()
    default_provider: str = ""
    default_model: str = ""
    system_prompt_extra: str = ""
    test_command: str = ""
    lint_command: str = ""
    watch_files: list[str] = []

    @classmethod
    def load(cls, path: Path | None = None) -> "ProjectConfig":
        search_path = path or Path.cwd()
        for parent in [search_path] + list(search_path.parents):
            config_file = parent / FARESTA_JSON_NAME
            if config_file.exists():
                try:
                    data = json.loads(config_file.read_text())
                    return cls(**data)
                except (json.JSONDecodeError, Exception):
                    pass
            if (parent / ".git").exists():
                break
        return cls()

    def save(self, path: Path | None = None):
        target = path or Path.cwd()
        filepath = target / FARESTA_JSON_NAME
        filepath.write_text(self.model_dump_json(indent=2))
        return filepath

    def is_tool_allowed(self, tool_name: str) -> bool:
        if tool_name in self.permissions.deny:
            return False
        if tool_name in self.permissions.allow:
            return True
        if tool_name in self.permissions.ask:
            return None
        return True