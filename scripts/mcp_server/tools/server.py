from __future__ import annotations

import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from mcp_server.config import (
    get_base_url,
    get_django_cmd,
    get_log_file,
    get_runserver_port,
    get_workspace_root,
)


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bb_status() -> dict[str, Any]:
        """Check if the Baby Buddy Django server is running and responding."""
        base = get_base_url()
        url = f"{base}/api/"
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return {"up": True, "status_code": resp.status, "url": url}
        except urllib.error.HTTPError as e:
            return {"up": True, "status_code": e.code, "url": url}
        except urllib.error.URLError as e:
            return {"up": False, "error": str(e.reason), "url": url}
        except OSError as e:
            return {"up": False, "error": str(e), "url": url}

    @mcp.tool()
    def bb_restart() -> dict[str, Any]:
        """Restart the dev server (manage.py runserver). Best-effort: may depend on how the server is run."""
        root = get_workspace_root()
        port = get_runserver_port()
        # Try to kill process on port (Linux/macOS)
        subprocess.run(
            ["fuser", "-k", f"{port}/tcp"],
            capture_output=True,
            check=False,
            cwd=root,
        )
        subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            check=False,
            cwd=root,
        )
        # Start runserver in background
        proc = subprocess.Popen(
            get_django_cmd(["runserver", str(port)]),
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return {"restarted": True, "port": port, "pid": proc.pid}

    @mcp.tool()
    def bb_logs(lines: int = 50, filter_text: str | None = None) -> dict[str, Any]:
        """Tail recent server logs; optionally filter by text. Set BB_LOG_FILE for log file path."""
        log_path = get_log_file()
        if log_path is None or not log_path.exists():
            return {
                "error": "No log file configured. Set BB_LOG_FILE to a path, or run the server with output redirected to a file.",
                "content": "",
            }
        try:
            content = log_path.read_text(encoding="utf-8", errors="replace")
            line_list = content.splitlines()
            if len(line_list) > lines:
                line_list = line_list[-lines:]
            if filter_text:
                needle = filter_text.lower()
                line_list = [ln for ln in line_list if needle in ln.lower()]
            return {"content": "\n".join(line_list), "path": str(log_path)}
        except OSError as e:
            return {"error": str(e), "content": ""}
