from __future__ import annotations

import re
import sqlite3
from typing import Any

from fastmcp import FastMCP

from mcp_server.config import get_database_url, get_db_path

# Allowed core app table names for bb_recent_entries (Django default naming).
CORE_TABLES = frozenset(
    {
        "core_bmi",
        "core_child",
        "core_diaperchange",
        "core_feeding",
        "core_headcircumference",
        "core_height",
        "core_note",
        "core_pumping",
        "core_sleep",
        "core_temperature",
        "core_timer",
        "core_tummytime",
        "core_weight",
        "core_medication",
        "core_medicationschedule",
        "core_tag",
        "core_tagged",
    }
)


def _sqlite_query(path: str, sql: str) -> list[dict[str, Any]]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        return [dict(zip(row.keys(), row)) for row in rows]
    finally:
        conn.close()


def _sqlite_recent(table: str, limit: int) -> list[dict[str, Any]]:
    path = str(get_db_path())
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    cur = conn.execute(f'SELECT * FROM "{table}" ORDER BY id DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(zip(row.keys(), row)) for row in rows]


def _postgres_query(database_url: str, sql: str) -> list[dict[str, Any]]:
    import psycopg2
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(database_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
    )
    cur = conn.cursor()
    try:
        cur.execute(sql)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    finally:
        cur.close()
        conn.close()


def _postgres_recent(database_url: str, table: str, limit: int) -> list[dict[str, Any]]:
    import psycopg2
    from urllib.parse import urlparse

    parsed = urlparse(database_url)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        dbname=parsed.path.lstrip("/"),
        user=parsed.username,
        password=parsed.password,
    )
    cur = conn.cursor()
    cur.execute('SELECT * FROM "{}" ORDER BY id DESC LIMIT %s'.format(table), (limit,))
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(zip(cols, row)) for row in rows]


def _is_read_only(sql: str) -> bool:
    """Allow only SELECT (no INSERT/UPDATE/DELETE/etc.)."""
    normalized = re.sub(r"\s+", " ", sql.strip()).upper()
    return normalized.startswith("SELECT")


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bb_db_query(sql: str) -> dict[str, Any]:
        """Run a read-only SQL query (SELECT only) against the Baby Buddy database. Returns a list of dicts (column names as keys)."""
        if not _is_read_only(sql):
            return {"error": "Only SELECT queries are allowed", "results": []}
        db_url = get_database_url()
        try:
            if db_url:
                results = _postgres_query(db_url, sql)
            else:
                results = _sqlite_query(str(get_db_path()), sql)
            return {"results": results}
        except Exception as e:
            return {"error": str(e), "results": []}

    @mcp.tool()
    def bb_recent_entries(model: str, limit: int = 10) -> dict[str, Any]:
        """Get recent entries from a core model table (e.g. core_feeding, core_diaperchange, core_sleep). Returns list of dicts."""
        if model not in CORE_TABLES:
            return {
                "error": f"Unknown model. Allowed: {sorted(CORE_TABLES)}",
                "results": [],
            }
        if limit < 1 or limit > 500:
            limit = min(max(1, limit), 500)
        try:
            db_url = get_database_url()
            if db_url:
                results = _postgres_recent(db_url, model, limit)
            else:
                results = _sqlite_recent(model, limit)
            return {"results": results}
        except Exception as e:
            return {"error": str(e), "results": []}
