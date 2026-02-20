# -*- coding: utf-8 -*-
"""Singleton MQTT client wrapper using paho-mqtt v2."""

import atexit
import logging
import os

import paho.mqtt.client as paho_mqtt
from django.db import close_old_connections

from .utils import get_mqtt_settings, get_topic_prefix

logger = logging.getLogger(__name__)


class MqttClient:
    """Thread-safe singleton wrapper around paho.mqtt.client.Client.

    - Reads connection settings from dbsettings (Site Settings page).
    - Sets a Last Will and Testament (LWT) for availability.
    - On (re)connect publishes ``online``, HA Discovery configs, and full state.
    - Uses ``loop_start()`` for a non-blocking background network thread.
    """

    def __init__(self):
        self._client = None
        self._started = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        """Connect to the broker and start the background loop."""
        if self._started:
            return

        s = get_mqtt_settings()
        prefix = get_topic_prefix()
        client_id = f"babybuddy_{os.getpid()}"

        self._client = paho_mqtt.Client(
            paho_mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )

        # Authentication
        username = s.username or ""
        password = s.password or ""
        if username:
            self._client.username_pw_set(username, password or None)

        # TLS
        if s.use_tls:
            self._client.tls_set()

        # LWT – broker publishes "offline" if we disconnect unexpectedly
        self._client.will_set(f"{prefix}/status", payload="offline", qos=1, retain=True)

        # Callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

        host = s.broker_host or "localhost"
        port = s.broker_port or 1883

        try:
            self._client.connect(host, port, keepalive=60)
            self._client.loop_start()
            self._started = True
            atexit.register(self.stop)
            logger.info("MQTT client started – connecting to %s:%s", host, port)
        except Exception:
            logger.exception("MQTT client failed to connect to %s:%s", host, port)

    def stop(self):
        """Publish offline status and disconnect gracefully."""
        if not self._started or self._client is None:
            return
        try:
            prefix = get_topic_prefix()
            self._client.publish(
                f"{prefix}/status", payload="offline", qos=1, retain=True
            )
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            logger.exception("Error stopping MQTT client")
        finally:
            self._started = False

    def reconnect(self):
        """Tear down the current connection and start fresh with current
        dbsettings values.  Safe to call even if not currently connected."""
        logger.info("MQTT client reconnecting with updated settings")
        self.stop()
        self._client = None
        self.start()

    def publish(self, topic, payload, retain=True, qos=1):
        """Publish a message. *payload* should be a string or bytes."""
        if not self._started or self._client is None:
            return
        try:
            self._client.publish(topic, payload=payload, qos=qos, retain=retain)
        except Exception:
            logger.exception("MQTT publish failed for topic %s", topic)

    @property
    def is_started(self):
        """Return ``True`` if the background loop has been started."""
        return self._started

    def is_connected(self):
        """Return ``True`` if the client is currently connected."""
        if self._client is None:
            return False
        return self._client.is_connected()

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info("MQTT connected to broker")
            prefix = get_topic_prefix()
            client.publish(f"{prefix}/status", payload="online", qos=1, retain=True)
            # Publish all discovery + state. This callback runs in paho's
            # network thread, so we close stale Django DB connections first.
            try:
                close_old_connections()

                # Both discovery and publisher import mqtt_client from
                # this module at top level, so importing them here avoids
                # a genuine circular import (client -> discovery/publisher
                # -> client).
                from .discovery import publish_all_discovery
                from .publisher import publish_all_state

                publish_all_discovery()
                publish_all_state()
            except Exception:
                logger.exception("Error publishing initial MQTT state")
        else:
            logger.warning("MQTT connect failed: reason_code=%s", reason_code)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties=None):
        if reason_code == 0:
            logger.info("MQTT disconnected cleanly")
        else:
            logger.warning("MQTT unexpected disconnect: reason_code=%s", reason_code)


# Module-level singleton – imported by other mqtt modules.
mqtt_client = MqttClient()
