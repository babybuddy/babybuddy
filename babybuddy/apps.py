# -*- coding: utf-8 -*-
import datetime
import os
import uuid

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

from dbsettings.loading import set_setting_value, setting_in_db

from babybuddy import VERSION


def create_read_only_group(sender, **kwargs):
    from django.contrib.auth.models import Group

    Group.objects.get_or_create(name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"])


def set_default_site_settings(sender, **kwargs):
    """
    Sets default values for site-wide settings.

    Based on `dbsettings.utils.set_defaults` which no longer seem to work in
    the latest versions of Django.
    """
    from babybuddy.config import config
    from core import models

    # Removed `NAP_START_MIN` and `NAP_START_MAX` values are referenced here
    # for pre-2.0.0 migrations.
    try:
        nap_start_min = datetime.datetime.strptime(
            os.environ.get("NAP_START_MIN"), "%H:%M"
        ).time()
    except (TypeError, ValueError):
        nap_start_min = models.Sleep.settings.nap_start_min
    try:
        nap_start_max = datetime.datetime.strptime(
            os.environ.get("NAP_START_MAX"), "%H:%M"
        ).time()
    except (TypeError, ValueError):
        nap_start_max = models.Sleep.settings.nap_start_max

    defaults = (
        ("Sleep", "nap_start_min", nap_start_min),
        ("Sleep", "nap_start_max", nap_start_max),
    )
    for class_name, attribute_name, value in defaults:
        if not setting_in_db("core.models", class_name, attribute_name):
            set_setting_value("core.models", class_name, attribute_name, value)

    # Seed MQTT settings from environment variables (first run only).
    # The module/class used here must match the registration in mqtt/settings.py
    # where the MqttSettings group is instantiated at module level.
    mqtt_module = "mqtt.settings"
    mqtt_class = ""  # module-level group, no owning model class
    mqtt_defaults = (
        ("enabled", config.mqtt_enabled),
        ("broker_host", config.mqtt_broker_host),
        ("broker_port", config.mqtt_broker_port),
        ("username", config.mqtt_username),
        ("password", config.mqtt_password),
        ("topic_prefix", config.mqtt_topic_prefix),
        ("use_tls", config.mqtt_tls),
    )
    for attribute_name, value in mqtt_defaults:
        if not setting_in_db(mqtt_module, mqtt_class, attribute_name):
            set_setting_value(mqtt_module, mqtt_class, attribute_name, value)

    # Seed Zeroconf / mDNS settings from environment variables (first run only).
    # Module is "babybuddy.zeroconf" (not site_settings) to avoid attribute
    # name collisions with MQTT settings in dbsettings storage.
    # Import the module so dbsettings registers the ZeroconfSettings group
    # before we attempt to read/write its keys.
    import babybuddy.zeroconf  # noqa: F401

    zc_module = "babybuddy.zeroconf"
    zc_class = ""
    zc_defaults = (
        ("enabled", config.zeroconf_enabled),
        ("advertised_port", config.zeroconf_port),
    )
    for attribute_name, value in zc_defaults:
        if not setting_in_db(zc_module, zc_class, attribute_name):
            set_setting_value(zc_module, zc_class, attribute_name, value)

    # Generate a stable instance_id (UUID4) on first run.
    if not setting_in_db(zc_module, zc_class, "instance_id"):
        set_setting_value(zc_module, zc_class, "instance_id", str(uuid.uuid4()))


class BabyBuddyConfig(AppConfig):
    name = "babybuddy"
    verbose_name = "Baby Buddy"
    version = VERSION
    version_string = VERSION

    def ready(self):
        post_migrate.connect(create_read_only_group, sender=self)
        post_migrate.connect(set_default_site_settings, sender=self)

        # Start Zeroconf mDNS advertising in a background thread, but
        # only when actually serving HTTP (runserver or gunicorn), not
        # during management commands like migrate, check, etc.
        if self._is_serving():
            try:
                from babybuddy.zeroconf import zeroconf_service

                zeroconf_service.start_in_background()
            except Exception as exc:
                import logging

                logging.getLogger("babybuddy.zeroconf").warning(
                    "Failed to start Zeroconf service: %s", exc
                )

    @staticmethod
    def _is_serving():
        """Return True if Django is starting as an HTTP server."""
        import sys

        # Django's runserver sets RUN_MAIN=true in the reloaded process.
        if os.environ.get("RUN_MAIN") == "true":
            return True
        # Gunicorn / uWSGI workers.
        if "gunicorn" in sys.modules or "uwsgi" in sys.modules:
            return True
        return False
