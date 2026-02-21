# -*- coding: utf-8 -*-
import datetime
import logging
import os
import uuid

from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

from dbsettings.loading import set_setting_value, setting_in_db

from babybuddy import VERSION

logger = logging.getLogger(__name__)

_zc_settings_dirty = False


def _on_zc_setting_changed(sender, **kwargs):
    """Flag that a Zeroconf setting changed during this request."""
    global _zc_settings_dirty
    if getattr(sender, "module_name", None) != "babybuddy.zeroconf":
        return
    _zc_settings_dirty = True
    logger.debug("Zeroconf setting '%s' changed", sender.attribute_name)


def _on_zc_request_finished(sender, **kwargs):
    """Re-register the Zeroconf mDNS service after settings change."""
    global _zc_settings_dirty
    if not _zc_settings_dirty:
        return
    _zc_settings_dirty = False

    from babybuddy.zeroconf import zeroconf_service

    zeroconf_service.stop()
    zeroconf_service.start()


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
    # where MqttConnectionSettings is instantiated at module level.
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
        from django.core.signals import request_finished

        from dbsettings.signals import setting_changed

        post_migrate.connect(create_read_only_group, sender=self)
        post_migrate.connect(set_default_site_settings, sender=self)

        setting_changed.connect(_on_zc_setting_changed)
        request_finished.connect(_on_zc_request_finished)

        if self._is_serving():
            self._check_uwsgi_threads()

            try:
                from babybuddy.zeroconf import zeroconf_service

                zeroconf_service.start_in_background()
            except Exception as exc:
                logger.warning("Failed to start Zeroconf service: %s", exc)

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

    @staticmethod
    def _check_uwsgi_threads():
        """Warn loudly if running under uWSGI without enable-threads."""
        try:
            import uwsgi

            if b"enable-threads" not in uwsgi.opt:
                logger.warning(
                    "uWSGI is running WITHOUT 'enable-threads'. "
                    "MQTT publishing, broker discovery, and Zeroconf "
                    "will NOT work. Add 'enable-threads = true' to "
                    "your uWSGI config and restart."
                )
        except ImportError:
            pass
