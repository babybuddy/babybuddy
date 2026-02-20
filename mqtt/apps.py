# -*- coding: utf-8 -*-
import logging

from django.apps import AppConfig
from django.core.signals import request_finished

from dbsettings.signals import setting_changed

logger = logging.getLogger(__name__)

_mqtt_settings_dirty = False


def _on_mqtt_setting_changed(sender, **kwargs):
    """Flag that MQTT settings changed during this request.

    The actual reconnect is deferred to ``request_finished`` so that all
    fields saved in one form submit are applied before reconnecting.
    """
    global _mqtt_settings_dirty
    if getattr(sender, "module_name", None) != "mqtt.settings":
        return
    _mqtt_settings_dirty = True
    logger.debug("MQTT setting '%s' changed", sender.attribute_name)


def _on_request_finished(sender, **kwargs):
    """Reconnect the MQTT client once, after the response is sent."""
    global _mqtt_settings_dirty
    if not _mqtt_settings_dirty:
        return
    _mqtt_settings_dirty = False

    from .client import mqtt_client

    if not mqtt_client.is_started:
        return
    logger.info("MQTT settings changed, reconnecting")
    mqtt_client.reconnect()


class MqttConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mqtt"
    verbose_name = "MQTT Publishing"

    def ready(self):
        # Import settings so dbsettings discovers the MqttSettings group.
        from . import settings  # noqa: F401 -- registers dbsettings group

        # Always register signal handlers.  The handlers themselves check
        # the dbsettings "enabled" toggle and lazily start/stop the MQTT
        # client, so toggling takes effect without a server restart.
        from . import signals  # noqa: F401 -- registers signal handlers

        setting_changed.connect(_on_mqtt_setting_changed)
        request_finished.connect(_on_request_finished)
