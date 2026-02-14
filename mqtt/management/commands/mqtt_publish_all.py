# -*- coding: utf-8 -*-
"""Management command to force re-publish all MQTT state and discovery."""

import time

from django.core.management.base import BaseCommand

from mqtt.client import mqtt_client
from mqtt.discovery import publish_all_discovery
from mqtt.publisher import publish_all_state
from mqtt.utils import get_mqtt_settings


class Command(BaseCommand):
    help = "Force re-publish all MQTT state and HA Discovery messages."

    def handle(self, *args, **options):
        settings = get_mqtt_settings()

        if not settings.enabled:
            self.stderr.write(
                self.style.WARNING(
                    "MQTT is disabled in Site Settings. "
                    "Enable it at /settings/ first."
                )
            )
            return

        if not mqtt_client.is_connected():
            mqtt_client.start()
            # Poll for connection (up to 10 seconds).
            for _ in range(20):
                if mqtt_client.is_connected():
                    break
                time.sleep(0.5)
            else:
                self.stderr.write(
                    self.style.ERROR(
                        "MQTT client could not connect within 10 seconds. "
                        "Check broker settings."
                    )
                )
                return

        publish_all_discovery()
        publish_all_state()
        self.stdout.write(
            self.style.SUCCESS("All MQTT discovery and state messages published.")
        )
