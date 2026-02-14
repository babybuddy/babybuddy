from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def get_workspace_root() -> Path:
    """Project root; resolve DB/template paths relative to this."""
    root = os.environ.get("BB_WORKSPACE_ROOT") or os.environ.get("WORKSPACE_ROOT")
    if root:
        return Path(root).resolve()
    return Path.cwd()


def get_base_url() -> str:
    """Baby Buddy base URL for API and status checks."""
    return os.environ.get("BB_BASE_URL", "http://127.0.0.1:8000").rstrip("/")


def get_api_token() -> str:
    """API token for REST auth.

    Priority:
    1. BB_API_TOKEN env (explicit override)
    2. Read first token from the DB (dynamic, zero-config)
    """
    token = os.environ.get("BB_API_TOKEN", "").strip()
    if token:
        return token
    return _token_from_db()


def _token_from_db() -> str:
    """Read the first API token from the database. Returns '' on any failure."""
    db_url = get_database_url()
    try:
        if db_url:
            return _token_from_pg(db_url)
        path = get_db_path()
        if not path.exists():
            return ""
        conn = sqlite3.connect(str(path))
        try:
            row = conn.execute(
                "SELECT t.key FROM authtoken_token t "
                "JOIN auth_user u ON t.user_id = u.id "
                "ORDER BY u.is_superuser DESC, u.id ASC LIMIT 1"
            ).fetchone()
            return row[0] if row else ""
        finally:
            conn.close()
    except Exception:
        return ""


def _token_from_pg(db_url: str) -> str:
    try:
        import psycopg2
        from urllib.parse import urlparse

        parsed = urlparse(db_url)
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            dbname=parsed.path.lstrip("/"),
            user=parsed.username,
            password=parsed.password,
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT t.key FROM authtoken_token t "
            "JOIN auth_user u ON t.user_id = u.id "
            "ORDER BY u.is_superuser DESC, u.id ASC LIMIT 1"
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else ""
    except Exception:
        return ""


def get_db_name() -> str:
    """Database name or path (SQLite file or Postgres DB name)."""
    return os.environ.get("DB_NAME", "data/db.sqlite3")


def get_database_url() -> str | None:
    """DATABASE_URL if set (Postgres); else None for SQLite."""
    return os.environ.get("DATABASE_URL")


def get_db_path() -> Path:
    """Resolved path for SQLite DB (when not using DATABASE_URL)."""
    name = get_db_name()
    if name.startswith("/"):
        return Path(name)
    return get_workspace_root() / name


def get_mqtt_host() -> str:
    return os.environ.get("MQTT_HOST", "localhost")


def get_mqtt_port() -> int:
    try:
        return int(os.environ.get("MQTT_PORT", "1883"))
    except ValueError:
        return 1883


def get_mqtt_user() -> str:
    return os.environ.get("MQTT_USER", "")


def get_mqtt_password() -> str:
    return os.environ.get("MQTT_PASSWORD", "")


def get_log_file() -> Path | None:
    """Optional server log file path for bb_logs."""
    path = os.environ.get("BB_LOG_FILE")
    if not path:
        return None
    p = Path(path)
    return p if p.is_absolute() else get_workspace_root() / path


def get_runserver_port() -> int:
    try:
        return int(os.environ.get("BB_RUNSERVER_PORT", "8000"))
    except ValueError:
        return 8000


def get_django_python() -> str:
    """Return path to the Python that has Django (the project venv).

    Checks .venv/bin/python under workspace root (pipenv with
    PIPENV_VENV_IN_PROJECT=1), then falls back to 'pipenv run python'.
    """
    venv_python = get_workspace_root() / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return "pipenv"


def get_django_cmd(manage_args: list[str]) -> list[str]:
    """Build a command list to run manage.py with the venv Python.

    Usage: get_django_cmd(["shell", "-c", code])
    Returns e.g. ["/workspaces/babybuddy/.venv/bin/python", "manage.py", "shell", "-c", code]
    """
    py = get_django_python()
    if py == "pipenv":
        return ["pipenv", "run", "python", "manage.py"] + manage_args
    return [py, "manage.py"] + manage_args
