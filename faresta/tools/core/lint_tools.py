import os
import subprocess
from pathlib import Path
from ..base import Tool


class LintTestTool(Tool):
    name = "lint_test"
    description = "Auto-detect and run linters/tests for the project. Detects pytest, ruff, flake8, eslint, npm test, go test, cargo test."
    parameters = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["test", "lint", "all"],
                "description": "What to run: 'test', 'lint', or 'all' (default: auto-detect)",
            },
            "path": {
                "type": "string",
                "description": "Project path (default: current working directory)",
            },
        },
        "required": [],
    }

    def execute(self, command: str = "all", path: str | None = None) -> str:
        cwd = Path(path).expanduser().resolve() if path else Path.cwd()
        results = []

        has_pyproject = (cwd / "pyproject.toml").exists() or any(cwd.glob("setup.py")) or any(cwd.glob("setup.cfg"))
        has_package = (cwd / "package.json").exists()
        has_go_mod = (cwd / "go.mod").exists()
        has_cargo = (cwd / "Cargo.toml").exists()

        if command in ("lint", "all"):
            if has_pyproject:
                for runner in ["ruff", "flake8", "pylint"]:
                    try:
                        r = subprocess.run(
                            [runner, "."],
                            capture_output=True, text=True, timeout=60, cwd=str(cwd),
                        )
                        output = r.stdout.strip() or r.stderr.strip()
                        results.append(f"{runner}: {'OK' if r.returncode == 0 else output[:2000]}")
                        break
                    except FileNotFoundError:
                        continue
            if has_package:
                for runner in ["npx eslint", "npx tsc --noEmit"]:
                    try:
                        r = subprocess.run(
                            runner.split(),
                            capture_output=True, text=True, timeout=60, cwd=str(cwd),
                        )
                        output = r.stdout.strip() or r.stderr.strip()
                        results.append(f"{runner}: {'OK' if r.returncode == 0 else output[:2000]}")
                    except FileNotFoundError:
                        continue

        if command in ("test", "all"):
            if has_pyproject:
                for runner in ["pytest", "python -m pytest"]:
                    try:
                        r = subprocess.run(
                            runner.split(),
                            capture_output=True, text=True, timeout=120, cwd=str(cwd),
                        )
                        output = r.stdout.strip() or r.stderr.strip()
                        results.append(f"{runner}: {'PASSED' if r.returncode == 0 else output[:2000]}")
                        break
                    except FileNotFoundError:
                        continue
            if has_package:
                for runner in ["npm test", "npm run test"]:
                    try:
                        r = subprocess.run(
                            runner.split(),
                            capture_output=True, text=True, timeout=120, cwd=str(cwd),
                        )
                        output = r.stdout.strip() or r.stderr.strip()
                        results.append(f"{runner}: {'PASSED' if r.returncode == 0 else output[:2000]}")
                        break
                    except FileNotFoundError:
                        continue
            if has_go_mod:
                r = subprocess.run(
                    ["go", "test", "./..."],
                    capture_output=True, text=True, timeout=120, cwd=str(cwd),
                )
                output = r.stdout.strip() or r.stderr.strip()
                results.append(f"go test: {'PASSED' if r.returncode == 0 else output[:2000]}")
            if has_cargo:
                r = subprocess.run(
                    ["cargo", "test"],
                    capture_output=True, text=True, timeout=120, cwd=str(cwd),
                )
                output = r.stdout.strip() or r.stderr.strip()
                results.append(f"cargo test: {'PASSED' if r.returncode == 0 else output[:2000]}")

        if not results:
            return "No recognized linter/test runner found in this project"
        return "\n\n".join(results)