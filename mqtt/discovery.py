# -*- coding: utf-8 -*-
"""Home Assistant MQTT Discovery config message builders.

Publishes retained config payloads to ``homeassistant/<component>/...`` topics
so that HA auto-creates entities for every Baby Buddy child.
"""

import json
import logging

from core.models import Child

from .client import mqtt_client
from .utils import get_mqtt_settings, get_topic_prefix

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Entity definitions
# ------------------------------------------------------------------

DISCOVERY_ENTITIES = {
    # -- "last entry" sensors --
    "last_feeding": {
        "component": "sensor",
        "name": "Last Feeding",
        "state_topic": "feeding/state",
        "value_template": "{{ value_json.end }}",
        "device_class": "timestamp",
        "json_attributes_topic": "feeding/state",
    },
    "last_diaper_change": {
        "component": "sensor",
        "name": "Last Diaper Change",
        "state_topic": "diaper_change/state",
        "value_template": "{{ value_json.time }}",
        "device_class": "timestamp",
        "json_attributes_topic": "diaper_change/state",
    },
    "last_sleep": {
        "component": "sensor",
        "name": "Last Sleep",
        "state_topic": "sleep/state",
        "value_template": "{{ value_json.end }}",
        "device_class": "timestamp",
        "json_attributes_topic": "sleep/state",
    },
    "last_pumping": {
        "component": "sensor",
        "name": "Last Pumping",
        "state_topic": "pumping/state",
        "value_template": "{{ value_json.end }}",
        "device_class": "timestamp",
        "json_attributes_topic": "pumping/state",
    },
    "last_tummy_time": {
        "component": "sensor",
        "name": "Last Tummy Time",
        "state_topic": "tummy_time/state",
        "value_template": "{{ value_json.end }}",
        "device_class": "timestamp",
        "json_attributes_topic": "tummy_time/state",
    },
    "last_note": {
        "component": "sensor",
        "name": "Last Note",
        "state_topic": "note/state",
        "value_template": "{{ value_json.time }}",
        "device_class": "timestamp",
        "json_attributes_topic": "note/state",
    },
    "last_medication": {
        "component": "sensor",
        "name": "Last Medication",
        "state_topic": "medication/state",
        "value_template": "{{ value_json.time }}",
        "device_class": "timestamp",
        "json_attributes_topic": "medication/state",
    },
    # -- measurement sensors --
    "temperature": {
        "component": "sensor",
        "name": "Temperature",
        "state_topic": "temperature/state",
        "value_template": "{{ value_json.temperature }}",
        "device_class": "temperature",
        "unit_of_measurement": "\u00b0C",
        "json_attributes_topic": "temperature/state",
    },
    "weight": {
        "component": "sensor",
        "name": "Weight",
        "state_topic": "weight/state",
        "value_template": "{{ value_json.weight }}",
        "device_class": "weight",
        "unit_of_measurement": "kg",
        "json_attributes_topic": "weight/state",
    },
    "height": {
        "component": "sensor",
        "name": "Height",
        "state_topic": "height/state",
        "value_template": "{{ value_json.height }}",
        "unit_of_measurement": "cm",
        "json_attributes_topic": "height/state",
    },
    "head_circumference": {
        "component": "sensor",
        "name": "Head Circumference",
        "state_topic": "head_circumference/state",
        "value_template": "{{ value_json.head_circumference }}",
        "unit_of_measurement": "cm",
        "json_attributes_topic": "head_circumference/state",
    },
    "bmi": {
        "component": "sensor",
        "name": "BMI",
        "state_topic": "bmi/state",
        "value_template": "{{ value_json.bmi }}",
        "json_attributes_topic": "bmi/state",
    },
    # -- daily aggregate sensors (from stats/state) --
    "feedings_today": {
        "component": "sensor",
        "name": "Feedings Today",
        "state_topic": "stats/state",
        "value_template": "{{ value_json.feedings_today }}",
    },
    "diaper_changes_today": {
        "component": "sensor",
        "name": "Diaper Changes Today",
        "state_topic": "stats/state",
        "value_template": "{{ value_json.diaper_changes_today }}",
    },
    "sleep_total_today": {
        "component": "sensor",
        "name": "Sleep Total Today",
        "state_topic": "stats/state",
        "value_template": "{{ value_json.sleep_total_today_minutes }}",
        "unit_of_measurement": "min",
    },
    "last_feeding_age": {
        "component": "sensor",
        "name": "Minutes Since Last Feeding",
        "state_topic": "stats/state",
        "value_template": "{{ value_json.last_feeding_minutes_ago }}",
        "unit_of_measurement": "min",
    },
    "last_diaper_change_age": {
        "component": "sensor",
        "name": "Minutes Since Last Diaper Change",
        "state_topic": "stats/state",
        "value_template": "{{ value_json.last_diaper_change_minutes_ago }}",
        "unit_of_measurement": "min",
    },
    # -- medication binary sensor --
    "medication_overdue": {
        "component": "binary_sensor",
        "name": "Medication Overdue",
        "state_topic": "stats/state",
        "value_template": (
            "{{ 'ON' if value_json.medications_overdue_count > 0 else 'OFF' }}"
        ),
        "device_class": "problem",
        "json_attributes_topic": "stats/state",
    },
    "medications_overdue_count": {
        "component": "sensor",
        "name": "Medications Overdue",
        "state_topic": "stats/state",
        "value_template": "{{ value_json.medications_overdue_count }}",
    },
}


# ------------------------------------------------------------------
# Publishing helpers
# ------------------------------------------------------------------


def _build_device(child):
    """Return the HA device dict for a child."""
    return {
        "identifiers": [f"babybuddy_{child.slug}"],
        "name": f"Baby Buddy - {child.first_name}",
        "manufacturer": "Baby Buddy",
        "model": "Child Tracker",
    }


def publish_child_discovery(child):
    """Publish all HA Discovery configs for a single *child* (retained).

    Respects the ``ha_discovery`` site setting -- if disabled, this is a no-op.
    """
    if not get_mqtt_settings().ha_discovery:
        return

    prefix = get_topic_prefix()
    device = _build_device(child)

    for entity_key, config in DISCOVERY_ENTITIES.items():
        component = config["component"]
        topic = f"homeassistant/{component}/babybuddy_{child.slug}/{entity_key}/config"
        payload = {
            "name": config["name"],
            "unique_id": f"babybuddy_{child.slug}_{entity_key}",
            "state_topic": f"{prefix}/{child.slug}/{config['state_topic']}",
            "value_template": config["value_template"],
            "availability_topic": f"{prefix}/status",
            "device": device,
        }
        if "device_class" in config:
            payload["device_class"] = config["device_class"]
        if "unit_of_measurement" in config:
            payload["unit_of_measurement"] = config["unit_of_measurement"]
        if "json_attributes_topic" in config:
            payload["json_attributes_topic"] = (
                f"{prefix}/{child.slug}/{config['json_attributes_topic']}"
            )

        mqtt_client.publish(topic, json.dumps(payload), retain=True)

    logger.info("Published HA Discovery for child %s", child.slug)


def remove_child_discovery(child):
    """Remove HA Discovery configs for a deleted *child* (empty payloads)."""
    for entity_key, config in DISCOVERY_ENTITIES.items():
        component = config["component"]
        topic = f"homeassistant/{component}/babybuddy_{child.slug}/{entity_key}/config"
        # Publishing an empty payload removes the entity from HA.
        mqtt_client.publish(topic, "", retain=True)

    logger.info("Removed HA Discovery for child %s", child.slug)


def publish_all_discovery():
    """Publish HA Discovery configs for all children.

    Respects the ``ha_discovery`` site setting -- if disabled, this is a no-op.
    """
    if not get_mqtt_settings().ha_discovery:
        return

    for child in Child.objects.all():
        publish_child_discovery(child)
