# -*- coding: utf-8 -*-
import datetime
import os

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
    from babybuddy.settings.base import strtobool
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
    # The module/class used here must match the registration in site_settings.py
    # where the MqttSettings group is instantiated at module level.
    mqtt_module = "babybuddy.site_settings"
    mqtt_class = ""  # module-level group, no owning model class
    mqtt_defaults = (
        (
            "enabled",
            bool(strtobool(os.environ.get("MQTT_ENABLED") or "False")),
        ),
        ("broker_host", os.environ.get("MQTT_BROKER_HOST", "localhost")),
        (
            "broker_port",
            int(os.environ.get("MQTT_BROKER_PORT", "1883")),
        ),
        ("username", os.environ.get("MQTT_USERNAME", "")),
        ("password", os.environ.get("MQTT_PASSWORD", "")),
        ("topic_prefix", os.environ.get("MQTT_TOPIC_PREFIX", "babybuddy")),
        (
            "use_tls",
            bool(strtobool(os.environ.get("MQTT_TLS") or "False")),
        ),
    )
    for attribute_name, value in mqtt_defaults:
        if not setting_in_db(mqtt_module, mqtt_class, attribute_name):
            set_setting_value(mqtt_module, mqtt_class, attribute_name, value)


class BabyBuddyConfig(AppConfig):
    name = "babybuddy"
    verbose_name = "Baby Buddy"
    version = VERSION
    version_string = VERSION

    def ready(self):
        post_migrate.connect(create_read_only_group, sender=self)
        post_migrate.connect(set_default_site_settings, sender=self)
