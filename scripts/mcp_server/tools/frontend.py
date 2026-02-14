from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from mcp_server.config import get_django_cmd, get_workspace_root

# Known app template and static dirs (relative to workspace).
TEMPLATE_APP_DIRS = (
    "babybuddy/templates",
    "core/templates",
    "dashboard/templates",
    "reports/templates",
)
STATIC_APP_DIRS = (
    "babybuddy/static",
    "core/static",
    "dashboard/static",
    "reports/static",
    "api/static",
)
STATIC_COLLECTED = "static"


def _template_dirs(root: Path) -> list[Path]:
    return [root / d for d in TEMPLATE_APP_DIRS if (root / d).is_dir()]


def _static_dirs(root: Path) -> list[Path]:
    out = [root / d for d in STATIC_APP_DIRS if (root / d).is_dir()]
    if (root / STATIC_COLLECTED).is_dir():
        out.append(root / STATIC_COLLECTED)
    return out


def _allowed_template_path(root: Path, path: Path) -> bool:
    """Path must be under root and under one of the template app dirs."""
    try:
        resolved = (root / path).resolve()
        resolved.relative_to(root)
    except (ValueError, RuntimeError):
        return False
    for d in TEMPLATE_APP_DIRS:
        base = root / d
        try:
            resolved.relative_to(base)
            return True
        except ValueError:
            continue
    return False


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bb_templates_list(app_filter: str | None = None) -> dict[str, Any]:
        """List Django template paths. Optionally filter by app: core, babybuddy, dashboard, reports."""
        root = get_workspace_root()
        if app_filter:
            subdir = f"{app_filter.strip().lower()}/templates"
            if subdir not in TEMPLATE_APP_DIRS:
                return {
                    "error": f"Unknown app. Use one of: babybuddy, core, dashboard, reports",
                    "paths": [],
                }
            dirs = [root / subdir] if (root / subdir).is_dir() else []
        else:
            dirs = _template_dirs(root)
        paths: list[str] = []
        for d in dirs:
            for f in d.rglob("*.html"):
                try:
                    rel = f.relative_to(root)
                    paths.append(str(rel))
                except ValueError:
                    continue
        paths.sort()
        return {"paths": paths}

    @mcp.tool()
    def bb_template_read(path: str) -> dict[str, Any]:
        """Read one template file. Path relative to workspace (e.g. core/templates/core/feeding_form.html)."""
        root = get_workspace_root()
        path_obj = Path(path)
        if path_obj.is_absolute() or ".." in path_obj.parts:
            return {"error": "Path must be relative and not contain ..", "content": ""}
        full = (root / path).resolve()
        if not _allowed_template_path(root, path_obj):
            return {
                "error": "Path must be under an app templates/ directory",
                "content": "",
            }
        if not full.exists() or not full.is_file():
            return {"error": "File not found", "content": ""}
        try:
            content = full.read_text(encoding="utf-8", errors="replace")
            return {"content": content, "path": path}
        except OSError as e:
            return {"error": str(e), "content": ""}

    @mcp.tool()
    def bb_static_list(subdir: str | None = None) -> dict[str, Any]:
        """List static files (CSS, JS, images). Optionally filter by subdir (e.g. babybuddy/js)."""
        root = get_workspace_root()
        dirs = _static_dirs(root)
        ext = (
            ".css",
            ".js",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".svg",
            ".ico",
            ".woff",
            ".woff2",
        )
        paths: list[str] = []
        subdir_norm = subdir.strip().lower().replace("\\", "/") if subdir else None
        for d in dirs:
            for f in d.rglob("*"):
                if f.is_file() and f.suffix.lower() in ext:
                    try:
                        rel = f.relative_to(root)
                        s = str(rel).replace("\\", "/")
                        if subdir_norm and subdir_norm not in s:
                            continue
                        paths.append(s)
                    except ValueError:
                        continue
        paths.sort()
        return {"paths": paths}

    @mcp.tool()
    def bb_urls_list() -> dict[str, Any]:
        """Expose URL map: run Django shell to list URL patterns, or fallback to URL module paths."""
        root = get_workspace_root()
        code = """
from django.urls import get_resolver
r = get_resolver()
def walk(prefix, p):
    for pat in p.url_patterns:
        if hasattr(pat, 'url_patterns'):
            walk(prefix + str(pat.pattern), pat)
        else:
            name = getattr(pat, 'name', None) or ''
            print(prefix + str(pat.pattern) + " -> " + name)
walk('', r)
"""
        result = subprocess.run(
            get_django_cmd(["shell", "-c", code]),
            cwd=root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode == 0 and result.stdout:
            lines = [
                ln.strip() for ln in result.stdout.strip().splitlines() if ln.strip()
            ]
            return {"urls": lines, "source": "django"}
        return {
            "urls": [],
            "source": "fallback",
            "note": "Django shell failed (e.g. no DB). URL modules: babybuddy/urls.py, api/urls.py, core/urls.py, dashboard/urls.py, reports/urls.py",
        }
