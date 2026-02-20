# -*- coding: utf-8 -*-
"""MQTT site-wide settings (dbsettings group).

Defined here so the mqtt app owns its own configuration. The module-level
instance is auto-discovered by dbsettings and rendered on the Site Settings
page (/settings/).
"""

from django.utils.translation import gettext_lazy as _

import dbsettings


class MqttSettings(dbsettings.Group):
    enabled = dbsettings.BooleanValue(
        default=False,
        description=_("Enable MQTT publishing"),
        help_text=_(
            "Publish model changes to an MQTT broker for Home Assistant "
            "integration. Toggling this takes effect immediately."
        ),
    )
    broker_host = dbsettings.StringValue(
        default="localhost",
        description=_("MQTT broker host"),
        help_text=_("Hostname or IP address of the MQTT broker."),
    )
    broker_port = dbsettings.PositiveIntegerValue(
        default=1883,
        description=_("MQTT broker port"),
        help_text=_("Port number for the MQTT broker (usually 1883, or 8883 for TLS)."),
    )
    username = dbsettings.StringValue(
        default="",
        required=False,
        description=_("MQTT username"),
        help_text=_(
            "Username for broker authentication (leave empty if not required)."
        ),
    )
    password = dbsettings.PasswordValue(
        default="",
        required=False,
        description=_("MQTT password"),
        help_text=_("Password for broker authentication."),
    )
    topic_prefix = dbsettings.StringValue(
        default="babybuddy",
        description=_("MQTT topic prefix"),
        help_text=_("Prefix for all MQTT topics (e.g. 'babybuddy')."),
    )
    use_tls = dbsettings.BooleanValue(
        default=False,
        description=_("Use TLS"),
        help_text=_("Enable TLS/SSL encryption for the broker connection."),
    )
    ha_discovery = dbsettings.BooleanValue(
        default=True,
        description=_("Publish Home Assistant MQTT discovery configs"),
        help_text=_(
            "When enabled, Baby Buddy publishes MQTT discovery config messages "
            "to homeassistant/sensor/... and homeassistant/binary_sensor/... "
            "topics so Home Assistant auto-creates entities. Disable this if "
            "you use the Baby Buddy HA integration (which reads "
            "/api/ha/discovery/ instead). Data topics are not affected."
        ),
    )


# Module-level instance — dbsettings auto-discovers this.
mqtt_settings = MqttSettings(_("MQTT"))
