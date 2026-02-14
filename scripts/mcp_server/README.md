# Baby Buddy MCP Dev Server

MCP (Model Context Protocol) server so Cursor can call tools against the running Baby Buddy instance: API, database, MQTT, server management, and frontend (templates, static, URLs).

## Run manually

From the **project root** (e.g. `/workspaces/babybuddy`):

```bash
PYTHONPATH=scripts python -m mcp_server
```

Cursor runs this via `.cursor/mcp.json` with `cwd` set to the repo root and `PYTHONPATH=scripts`.

## API authentication

The MCP server reads the API token **dynamically from the database** at runtime (picks the first superuser's token, or the first user's). No setup needed -- if a user with a token exists, API tools authenticate automatically.

You can override with `BB_API_TOKEN` env if needed, but normally you don't have to.

## Environment variables

All optional. Sensible defaults work in the dev container.

| Variable                      | Default                        | Description                                    |
| ----------------------------- | ------------------------------ | ---------------------------------------------- |
| `BB_PORT`                     | `8282`                         | Baby Buddy port (single source of truth)       |
| `BB_BASE_URL`                 | `http://127.0.0.1:${BB_PORT}` | Baby Buddy base URL (derived from BB_PORT)     |
| `BB_API_TOKEN`                | (from DB)                      | Override: API token for REST auth              |
| `BB_WORKSPACE_ROOT`           | cwd                            | Project root for DB/template paths             |
| `DATABASE_URL`                | (none)                         | Postgres URL; if unset, SQLite is used         |
| `DB_NAME`                     | `data/db.sqlite3`              | SQLite path (relative to workspace)            |
| `MQTT_HOST`                   | `localhost`                    | MQTT broker host                               |
| `MQTT_PORT`                   | `1883`                         | MQTT broker port                               |
| `MQTT_USER` / `MQTT_PASSWORD` | (none)                         | Optional broker auth                           |
| `BB_LOG_FILE`                 | (none)                         | Optional path to server log file for `bb_logs` |
| `BB_RUNSERVER_PORT`           | (from `BB_PORT`)               | Override port for `bb_restart` / status        |
