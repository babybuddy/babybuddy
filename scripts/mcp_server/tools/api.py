from __future__ import annotations

import json
import secrets
import sqlite3
import urllib.error
import urllib.request
from typing import Any

from fastmcp import FastMCP

from mcp_server.config import get_base_url, get_api_token, get_database_url, get_db_path


def _request(
    method: str,
    endpoint: str,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base = get_base_url()
    path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    url = f"{base}{path}"
    token = get_api_token()
    headers: dict[str, str] = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"
    if data is not None:
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, method=method, headers=headers)
    if data is not None:
        req.data = json.dumps(data).encode("utf-8")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = raw
            return {"status": resp.status, "body": body}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8") if e.fp else str(e)
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = raw
        return {"status": e.code, "body": body}
    except urllib.error.URLError as e:
        return {"status": 0, "body": f"Connection error: {e.reason}"}
    except OSError as e:
        return {"status": 0, "body": str(e)}


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def bb_api_get(endpoint: str) -> dict[str, Any]:
        """GET any Baby Buddy API endpoint. Returns status and JSON body (or error text)."""
        return _request("GET", endpoint)

    @mcp.tool()
    def bb_api_post(endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """POST to any Baby Buddy API endpoint with JSON body. Returns status and response body."""
        return _request("POST", endpoint, data=data)

    @mcp.tool()
    def bb_child_list() -> dict[str, Any]:
        """List all children from the Baby Buddy API."""
        return _request("GET", "/api/children/")

    @mcp.tool()
    def bb_child_stats(slug: str) -> dict[str, Any]:
        """Get stats for a child (GET /api/children/{slug}/stats/)."""
        return _request("GET", f"/api/children/{slug}/stats/")

    @mcp.tool()
    def bb_get_or_create_api_token(username: str | None = None) -> dict[str, Any]:
        """Get or create an API token for a user. Returns the token; set BB_API_TOKEN to this value in your environment (e.g. in .cursor/mcp.json env or shell) and restart the MCP server so API tools can authenticate. Does not write the token to disk."""
        db_url = get_database_url()
        try:
            if db_url:
                return _get_or_create_token_pg(db_url, username)
            return _get_or_create_token_sqlite(str(get_db_path()), username)
        except Exception as e:
            return {"ok": False, "error": str(e)}


def _get_or_create_token_sqlite(path: str, username: str | None) -> dict[str, Any]:
    conn = sqlite3.connect(path)
    try:
        if username:
            row = conn.execute(
                "SELECT id, username FROM auth_user WHERE username = ?", (username,)
            ).fetchone()
            if not row:
                return {"ok": False, "error": f"No user with username: {username!r}"}
        else:
            row = conn.execute(
                "SELECT id, username FROM auth_user WHERE is_superuser = 1 ORDER BY id LIMIT 1"
            ).fetchone()
            if not row:
                row = conn.execute(
                    "SELECT id, username FROM auth_user ORDER BY id LIMIT 1"
                ).fetchone()
            if not row:
                return {"ok": False, "error": "No user in database"}
        user_id, user_name = row
        token_row = conn.execute(
            "SELECT key FROM authtoken_token WHERE user_id = ?", (user_id,)
        ).fetchone()
        if token_row:
            return _token_result(token_row[0], user_name, created=False)
        key = secrets.token_hex(20)
        conn.execute(
            "INSERT INTO authtoken_token (key, user_id, created) VALUES (?, ?, datetime('now'))",
            (key, user_id),
        )
        conn.commit()
        return _token_result(key, user_name, created=True)
    finally:
        conn.close()


def _get_or_create_token_pg(db_url: str, username: str | None) -> dict[str, Any]:
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
    try:
        if username:
            cur.execute(
                "SELECT id, username FROM auth_user WHERE username = %s", (username,)
            )
            row = cur.fetchone()
            if not row:
                return {"ok": False, "error": f"No user with username: {username!r}"}
        else:
            cur.execute(
                "SELECT id, username FROM auth_user WHERE is_superuser = true ORDER BY id LIMIT 1"
            )
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT id, username FROM auth_user ORDER BY id LIMIT 1")
                row = cur.fetchone()
            if not row:
                return {"ok": False, "error": "No user in database"}
        user_id, user_name = row
        cur.execute("SELECT key FROM authtoken_token WHERE user_id = %s", (user_id,))
        token_row = cur.fetchone()
        if token_row:
            return _token_result(token_row[0], user_name, created=False)
        key = secrets.token_hex(20)
        cur.execute(
            "INSERT INTO authtoken_token (key, user_id, created) VALUES (%s, %s, now())",
            (key, user_id),
        )
        conn.commit()
        return _token_result(key, user_name, created=True)
    finally:
        cur.close()
        conn.close()


def _token_result(key: str, user: str, created: bool) -> dict[str, Any]:
    return {
        "ok": True,
        "token": key,
        "user": user,
        "created": created,
        "instructions": "Set BB_API_TOKEN to the token above in your environment "
        "(e.g. in .cursor/mcp.json under env, or in your shell) and restart "
        "the MCP server so API tools authenticate.",
    }
