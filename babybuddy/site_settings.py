# -*- coding: utf-8 -*-
from datetime import time

from django.utils.translation import gettext_lazy as _

import dbsettings

from core.fields import NapStartMaxTimeField, NapStartMinTimeField
from .widgets import TimeInput


class NapStartMaxTimeValue(dbsettings.TimeValue):
    field = NapStartMaxTimeField


class NapStartMinTimeValue(dbsettings.TimeValue):
    field = NapStartMinTimeField


class NapSettings(dbsettings.Group):
    nap_start_min = NapStartMinTimeValue(
        default=time(6),
        description=_("Default minimum nap start time"),
        help_text=_(
            "The minimum default time that a sleep entry is consider a nap. If set the nap property will be preselected if the start time is within the bounds."
        ),
        widget=TimeInput,
    )
    nap_start_max = NapStartMaxTimeValue(
        default=time(18),
        description=_("Default maximum nap start time"),
        help_text=_(
            "The maximum default time that a sleep entry is consider a nap. If set the nap property will be preselected if the start time is within the bounds."
        ),
        widget=TimeInput,
    )


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
        help_text=_(
            "Hostname or IP address of the MQTT broker. "
            "Changing this requires a server restart."
        ),
    )
    broker_port = dbsettings.PositiveIntegerValue(
        default=1883,
        description=_("MQTT broker port"),
        help_text=_(
            "Port number for the MQTT broker (usually 1883, or 8883 for TLS). "
            "Changing this requires a server restart."
        ),
    )
    username = dbsettings.StringValue(
        default="",
        required=False,
        description=_("MQTT username"),
        help_text=_(
            "Username for broker authentication (leave empty if not required). "
            "Changing this requires a server restart."
        ),
    )
    password = dbsettings.PasswordValue(
        default="",
        required=False,
        description=_("MQTT password"),
        help_text=_(
            "Password for broker authentication. "
            "Changing this requires a server restart."
        ),
    )
    topic_prefix = dbsettings.StringValue(
        default="babybuddy",
        description=_("MQTT topic prefix"),
        help_text=_(
            "Prefix for all MQTT topics (e.g. 'babybuddy'). "
            "Changing this requires a server restart."
        ),
    )
    use_tls = dbsettings.BooleanValue(
        default=False,
        description=_("Use TLS"),
        help_text=_(
            "Enable TLS/SSL encryption for the broker connection. "
            "Changing this requires a server restart."
        ),
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


# Module-level instances — dbsettings auto-discovers these and renders
# them on the Site Settings page (/settings/).
mqtt = MqttSettings(_("MQTT"))
