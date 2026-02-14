# -*- coding: utf-8 -*-
"""Central configuration for Baby Buddy.

All Baby-Buddy-specific environment variables are read here once, exposed
as typed attributes on a frozen dataclass, and imported everywhere else::

    from babybuddy.config import config

    port = config.bb_port          # int
    path = config.sub_path         # str

This module has **no Django dependency** so it can be imported safely from
``settings/base.py``, ``gunicorn.py``, the MCP helper, etc.

`python-dotenv` must call ``load_dotenv()`` *before* this module is first
imported if you want ``.env`` values picked up.  In the Django path that
happens at the top of ``settings/base.py``; standalone scripts should call
``load_dotenv()`` themselves.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _bool(val: str | None, default: bool = False) -> bool:
    """Convert an env-var string to bool (same logic as the old strtobool)."""
    if val is None:
        return default
    val = val.strip().lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    if val in ("n", "no", "f", "false", "off", "0"):
        return False
    return default


def _int(val: str | None, default: int) -> int:
    try:
        return int(val) if val else default
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Config:
    """Typed, read-once configuration sourced from environment variables.

    Every attribute corresponds to one ``os.environ`` key (listed in the
    inline comments).  Defaults match what the project has historically
    shipped so this is fully backwards-compatible.
    """

    # -- Server ---------------------------------------------------------------
    bb_port: int = field(  # BB_PORT
        default_factory=lambda: _int(os.environ.get("BB_PORT"), 8282)
    )
    sub_path: str = field(  # SUB_PATH
        default_factory=lambda: os.environ.get("SUB_PATH", "")
    )
    debug: bool = field(default_factory=lambda: _bool(os.environ.get("DEBUG")))  # DEBUG
    secret_key: str = field(  # SECRET_KEY
        default_factory=lambda: os.environ.get("SECRET_KEY") or ""
    )
    allowed_hosts: str = field(  # ALLOWED_HOSTS
        default_factory=lambda: os.environ.get("ALLOWED_HOSTS", "*")
    )

    # -- Zeroconf seeding (first-run only) ------------------------------------
    zeroconf_enabled: bool = field(  # ZEROCONF_ENABLED
        default_factory=lambda: _bool(os.environ.get("ZEROCONF_ENABLED"), default=True)
    )
    zeroconf_port: int = field(  # ZEROCONF_PORT → BB_PORT
        default_factory=lambda: _int(
            os.environ.get("ZEROCONF_PORT") or os.environ.get("BB_PORT"), 8282
        )
    )

    # -- MQTT seeding (first-run only) ----------------------------------------
    mqtt_enabled: bool = field(  # MQTT_ENABLED
        default_factory=lambda: _bool(os.environ.get("MQTT_ENABLED"))
    )
    mqtt_broker_host: str = field(  # MQTT_BROKER_HOST
        default_factory=lambda: os.environ.get("MQTT_BROKER_HOST", "localhost")
    )
    mqtt_broker_port: int = field(  # MQTT_BROKER_PORT
        default_factory=lambda: _int(os.environ.get("MQTT_BROKER_PORT"), 1883)
    )
    mqtt_username: str = field(  # MQTT_USERNAME
        default_factory=lambda: os.environ.get("MQTT_USERNAME", "")
    )
    mqtt_password: str = field(  # MQTT_PASSWORD
        default_factory=lambda: os.environ.get("MQTT_PASSWORD", "")
    )
    mqtt_topic_prefix: str = field(  # MQTT_TOPIC_PREFIX
        default_factory=lambda: os.environ.get("MQTT_TOPIC_PREFIX", "babybuddy")
    )
    mqtt_tls: bool = field(  # MQTT_TLS
        default_factory=lambda: _bool(os.environ.get("MQTT_TLS"))
    )

    # -- Home Assistant -------------------------------------------------------
    enable_home_assistant: bool = field(  # ENABLE_HOME_ASSISTANT_SUPPORT
        default_factory=lambda: _bool(os.environ.get("ENABLE_HOME_ASSISTANT_SUPPORT"))
    )

    # -- Misc -----------------------------------------------------------------
    reverse_proxy_auth: bool = field(  # REVERSE_PROXY_AUTH
        default_factory=lambda: _bool(os.environ.get("REVERSE_PROXY_AUTH"))
    )
    allow_uploads: bool = field(  # ALLOW_UPLOADS
        default_factory=lambda: _bool(os.environ.get("ALLOW_UPLOADS"), default=True)
    )

    # -- Helpers --------------------------------------------------------------

    @property
    def allowed_hosts_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",")]


# Singleton — instantiated once at import time.
config = Config()
