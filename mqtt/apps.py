# -*- coding: utf-8 -*-
from django.apps import AppConfig


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
