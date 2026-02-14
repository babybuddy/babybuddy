# -*- coding: utf-8 -*-
"""Shared helpers for the mqtt app."""

from babybuddy.site_settings import mqtt as _mqtt_settings


def get_mqtt_settings():
    """Return the MqttSettings dbsettings group instance."""
    return _mqtt_settings


def get_topic_prefix():
    """Return the configured MQTT topic prefix (default ``'babybuddy'``)."""
    return get_mqtt_settings().topic_prefix or "babybuddy"
