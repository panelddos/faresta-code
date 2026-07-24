import os
from pathlib import Path
from ..base import Tool


class ProjectIndexTool(Tool):
    name = "project_index"
    description = "Scan the project root and return its structure: directory tree, README summary, dependencies, and config files."
    parameters = {
        "type": "object",
        "properties": {
            "depth": {
                "type": "integer",
                "description": "Directory tree depth (default 3, max 5)",
                "default": 3,
            },
            "path": {
                "type": "string",
                "description": "Project root path (default: current working directory)",
            },
        },
        "required": [],
    }

    def execute(self, depth: int = 3, path: str | None = None) -> str:
        root = Path(path).expanduser().resolve() if path else Path.cwd()
        if not root.is_dir():
            return f"Error: not a directory: {root}"

        parts = []

        name = root.name
        parts.append(f"Project: {name}")
        parts.append(f"Root: {root}")

        summary = self._read_summary(root)
        if summary:
            parts.append(f"\n--- README ---\n{summary}")

        deps = self._detect_deps(root)
        if deps:
            parts.append(f"\n--- Dependencies ({deps['type']}) ---")
            parts.extend(f"  - {d}" for d in deps["packages"])

        ignore_dirs = {
            ".git", "__pycache__", "node_modules", ".venv", "env",
            "venv", ".tox", "dist", "build", ".egg-info",
            ".opencode", ".faresta", ".github", ".vscode", "target",
        }
        ignore_ext = {".pyc", ".pyo", ".so", ".o", ".class"}

        parts.append(f"\n--- Directory Tree (depth={depth}) ---")
        tree_lines = self._build_tree(root, max_depth=depth, ignore_dirs=ignore_dirs, ignore_ext=ignore_ext)
        parts.extend(tree_lines)

        return "\n".join(parts)

    def _read_summary(self, root: Path) -> str | None:
        for name in ("README.md", "README.txt", "README", "Readme.md"):
            f = root / name
            if f.exists() and f.is_file():
                try:
                    content = f.read_text(encoding="utf-8", errors="replace")
                    lines = content.strip().split("\n")
                    summary_lines = [l for l in lines if l.strip()][:15]
                    return "\n".join(summary_lines)
                except Exception:
                    return None
        return None

    def _detect_deps(self, root: Path) -> dict | None:
        pkg_json = root / "package.json"
        if pkg_json.exists():
            try:
                import json
                data = json.loads(pkg_json.read_text(encoding="utf-8"))
                deps = {}
                deps.update(data.get("dependencies", {}))
                deps.update(data.get("devDependencies", {}))
                return {"type": "npm", "packages": [f"{k}@{v}" for k, v in deps.items()]}
            except Exception:
                pass

        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                text = pyproject.read_text(encoding="utf-8")
                lines = [l.strip() for l in text.split("\n") if "=" in l and not l.strip().startswith("#")]
                pkgs = []
                for l in lines:
                    if l.startswith('"') or l.startswith("'"):
                        pkgs.append(l.strip(", "))
                return {"type": "python (pyproject.toml)", "packages": pkgs[:30]}
            except Exception:
                pass

        req = root / "requirements.txt"
        if req.exists():
            try:
                lines = [l.strip() for l in req.read_text(encoding="utf-8").split("\n") if l.strip() and not l.startswith("#")]
                return {"type": "pip", "packages": lines[:30]}
            except Exception:
                pass

        go_mod = root / "go.mod"
        if go_mod.exists():
            try:
                lines = [l.strip() for l in go_mod.read_text(encoding="utf-8").split("\n") if l.strip() and l.startswith("\t")]
                return {"type": "go", "packages": lines[:30]}
            except Exception:
                pass

        cargo = root / "Cargo.toml"
        if cargo.exists():
            try:
                text = cargo.read_text(encoding="utf-8")
                lines = [l.strip() for l in text.split("\n") if "=" in l]
                pkgs = [l for l in lines if not l.startswith("[")]
                return {"type": "rust", "packages": pkgs[:30]}
            except Exception:
                pass

        return None

    def _build_tree(
        self, root: Path, prefix: str = "", max_depth: int = 3,
        ignore_dirs: set | None = None, ignore_ext: set | None = None,
        depth: int = 0,
    ) -> list[str]:
        if depth >= max_depth:
            return ["  " * depth + "..."]

        ignore_dirs = ignore_dirs or set()
        ignore_ext = ignore_ext or set()
        lines = []

        try:
            entries = sorted(
                root.iterdir(),
                key=lambda e: (not e.is_dir(), e.name.lower()),
            )
        except PermissionError:
            return []

        filtered = []
        for e in entries:
            if e.name in ignore_dirs or (e.suffix in ignore_ext and e.is_file()):
                continue
            if e.name.startswith(".") and e.name not in (".env", ".gitignore", ".env.example"):
                continue
            filtered.append(e)

        for i, entry in enumerate(filtered):
            is_last = i == len(filtered) - 1
            connector = "└── " if is_last else "├── "
            sub_prefix = "    " if is_last else "│   "
            if entry.is_dir():
                lines.append(prefix + connector + f"[{entry.name}/]")
                lines.extend(
                    self._build_tree(
                        entry, prefix + sub_prefix, max_depth,
                        ignore_dirs, ignore_ext, depth + 1,
                    )
                )
            else:
                try:
                    size = entry.stat().st_size
                    size_str = f" ({self._fmt_size(size)})" if size > 0 else ""
                    lines.append(prefix + connector + f"{entry.name}{size_str}")
                except OSError:
                    lines.append(prefix + connector + f"{entry.name}")

        return lines

    @staticmethod
    def _fmt_size(b: int) -> str:
        if b < 1024:
            return f"{b}B"
        elif b < 1024**2:
            return f"{b/1024:.1f}K"
        else:
            return f"{b/1024**2:.1f}M"
