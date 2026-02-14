from __future__ import annotations

import socket
import subprocess
from typing import Any

from fastmcp import FastMCP

from mcp_server.config import (
    get_django_python,
    get_mqtt_host,
    get_mqtt_port,
    get_mqtt_user,
    get_mqtt_password,
)


def _broker_listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except (OSError, socket.error):
        return False


def register(mcp: FastMCP) -> None:
    @mcp.tool()
    def mqtt_publish(topic: str, payload: str) -> dict[str, Any]:
        """Publish a message to the MQTT broker using paho-mqtt."""
        host = get_mqtt_host()
        port = get_mqtt_port()
        user = get_mqtt_user()
        pwd = get_mqtt_password()
        auth = f", auth={{'username': {user!r}, 'password': {pwd!r}}}" if user else ""
        code = (
            "import paho.mqtt.publish as pub; "
            f"pub.single({topic!r}, {payload!r}, hostname={host!r}, port={port}{auth}); "
            "print('ok')"
        )
        py = get_django_python()  # venv Python has paho-mqtt
        result = subprocess.run(
            [py, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0 and "ok" in result.stdout:
            return {"ok": True, "topic": topic, "host": host, "port": port}
        return {
            "ok": False,
            "error": result.stderr.strip()
            or result.stdout.strip()
            or "paho publish failed",
            "host": host,
            "port": port,
        }

    @mcp.tool()
    def mqtt_ensure_broker() -> dict[str, Any]:
        """Check if the MQTT broker is running; start it in the background if not."""
        host = get_mqtt_host()
        port = get_mqtt_port()
        if _broker_listening(host, port):
            return {"status": "already running", "host": host, "port": port}
        # Try to start mosquitto locally (only works if installed)
        try:
            subprocess.Popen(
                ["mosquitto", "-p", str(port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return {"status": "started in background", "host": host, "port": port}
        except FileNotFoundError:
            return {
                "status": "broker not reachable and mosquitto not installed",
                "host": host,
                "port": port,
                "hint": "Set MQTT_HOST to the broker's hostname if it runs in another container.",
            }
