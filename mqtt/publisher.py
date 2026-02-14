# -*- coding: utf-8 -*-
"""Signal handlers that serialize model instances and publish to MQTT."""

import json
import logging

from core.models import (
    BMI,
    Child,
    DiaperChange,
    Feeding,
    HeadCircumference,
    Height,
    Medication,
    MedicationSchedule,
    Note,
    Pumping,
    Sleep,
    Temperature,
    Timer,
    TummyTime,
    Weight,
)

from .client import mqtt_client
from .discovery import publish_child_discovery, remove_child_discovery
from .serializers import (
    MqttBMISerializer,
    MqttChildSerializer,
    MqttDiaperChangeSerializer,
    MqttFeedingSerializer,
    MqttHeadCircumferenceSerializer,
    MqttHeightSerializer,
    MqttMedicationScheduleSerializer,
    MqttMedicationSerializer,
    MqttNoteSerializer,
    MqttPumpingSerializer,
    MqttSleepSerializer,
    MqttTemperatureSerializer,
    MqttTimerSerializer,
    MqttTummyTimeSerializer,
    MqttWeightSerializer,
)
from .stats import compute_stats
from .utils import get_mqtt_settings, get_topic_prefix

logger = logging.getLogger(__name__)

# Maps each model class to its MQTT topic segment.
MODEL_TOPIC_MAP = {
    BMI: "bmi",
    Child: "child",
    DiaperChange: "diaper_change",
    Feeding: "feeding",
    HeadCircumference: "head_circumference",
    Height: "height",
    Medication: "medication",
    MedicationSchedule: "medication_schedule",
    Note: "note",
    Pumping: "pumping",
    Sleep: "sleep",
    Temperature: "temperature",
    Timer: "timer",
    TummyTime: "tummy_time",
    Weight: "weight",
}

# Maps each model class to its MQTT serializer.
MODEL_SERIALIZER_MAP = {
    BMI: MqttBMISerializer,
    Child: MqttChildSerializer,
    DiaperChange: MqttDiaperChangeSerializer,
    Feeding: MqttFeedingSerializer,
    HeadCircumference: MqttHeadCircumferenceSerializer,
    Height: MqttHeightSerializer,
    Medication: MqttMedicationSerializer,
    MedicationSchedule: MqttMedicationScheduleSerializer,
    Note: MqttNoteSerializer,
    Pumping: MqttPumpingSerializer,
    Sleep: MqttSleepSerializer,
    Temperature: MqttTemperatureSerializer,
    Timer: MqttTimerSerializer,
    TummyTime: MqttTummyTimeSerializer,
    Weight: MqttWeightSerializer,
}

# Ordering field used to find the latest entry for each model.
MODEL_ORDER_FIELD = {
    BMI: "-date",
    DiaperChange: "-time",
    Feeding: "-end",
    HeadCircumference: "-date",
    Height: "-date",
    Medication: "-time",
    Note: "-time",
    Pumping: "-end",
    Sleep: "-end",
    Temperature: "-time",
    Timer: "-start",
    TummyTime: "-end",
    Weight: "-date",
}


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _get_child(instance):
    """Return the ``Child`` associated with *instance*, or ``None``."""
    if isinstance(instance, Child):
        return instance
    child = getattr(instance, "child", None)
    return child


def _serialize(model_class, instance, child):
    """Serialize *instance* to a JSON-encodable dict."""
    serializer_class = MODEL_SERIALIZER_MAP.get(model_class)
    if serializer_class is None:
        return None
    return serializer_class(instance).data


def _ensure_client():
    """Check the dbsettings toggle and lazily start or stop the MQTT client.

    Returns ``True`` if publishing should proceed, ``False`` otherwise.
    """
    s = get_mqtt_settings()

    if s.enabled:
        if not mqtt_client.is_started:
            mqtt_client.start()
        return True
    else:
        # MQTT was disabled — if the client is still running, stop it.
        if mqtt_client.is_started:
            mqtt_client.stop()
        return False


def _publish_stats(child):
    """Compute and publish daily stats for *child*."""
    prefix = get_topic_prefix()
    try:
        stats = compute_stats(child)
        topic = f"{prefix}/{child.slug}/stats/state"
        mqtt_client.publish(topic, json.dumps(stats, default=str))
    except Exception:
        logger.exception("Error publishing stats for child %s", child.slug)


# ------------------------------------------------------------------
# Signal handlers
# ------------------------------------------------------------------


def on_model_save(sender, instance, created, **kwargs):
    """Publish updated state when a core model is saved."""
    if not _ensure_client():
        return

    child = _get_child(instance)
    if child is None:
        return

    prefix = get_topic_prefix()
    model_key = MODEL_TOPIC_MAP.get(sender)
    if model_key is None:
        return

    # For MedicationSchedule, publish the full list of active schedules.
    if sender is MedicationSchedule:
        _publish_medication_schedules(child, mqtt_client, prefix)
    else:
        payload = _serialize(sender, instance, child)
        topic = f"{prefix}/{child.slug}/{model_key}/state"
        mqtt_client.publish(topic, json.dumps(payload, default=str))

    # Child creation triggers discovery for new child.
    if sender is Child and created:
        try:
            publish_child_discovery(child)
        except Exception:
            logger.exception("Error publishing discovery for new child %s", child.slug)

    _publish_stats(child)


def on_model_delete(sender, instance, **kwargs):
    """Re-publish state after deletion (show previous entry or null)."""
    if not _ensure_client():
        return

    child = _get_child(instance)
    if child is None:
        return

    prefix = get_topic_prefix()
    model_key = MODEL_TOPIC_MAP.get(sender)
    if model_key is None:
        return

    if sender is MedicationSchedule:
        _publish_medication_schedules(child, mqtt_client, prefix)
    elif sender is Child:
        # Remove discovery configs by publishing empty payloads.
        try:
            remove_child_discovery(child)
        except Exception:
            logger.exception("Error removing discovery for child %s", child.slug)
        return  # No stats to publish for a deleted child.
    else:
        order_field = MODEL_ORDER_FIELD.get(sender, "-id")
        latest = sender.objects.filter(child=child).order_by(order_field).first()
        payload = _serialize(sender, latest, child) if latest else None
        topic = f"{prefix}/{child.slug}/{model_key}/state"
        mqtt_client.publish(topic, json.dumps(payload, default=str))

    _publish_stats(child)


# ------------------------------------------------------------------
# Bulk publish (called on connect / reconnect)
# ------------------------------------------------------------------


def _publish_medication_schedules(child, client, prefix):
    """Publish all active medication schedules for *child* as a list."""
    schedules = MedicationSchedule.objects.filter(child=child, active=True)
    serializer = MqttMedicationScheduleSerializer(schedules, many=True)
    topic = f"{prefix}/{child.slug}/medication_schedule/state"
    client.publish(topic, json.dumps(serializer.data, default=str))


def publish_all_state():
    """Publish current state for every child and every model.

    Called on MQTT (re)connect so that retained topics are up-to-date.
    """
    prefix = get_topic_prefix()

    for child in Child.objects.all():
        # Child info
        payload = _serialize(Child, child, child)
        mqtt_client.publish(
            f"{prefix}/{child.slug}/child/state",
            json.dumps(payload, default=str),
        )

        # Last entry for each event model
        for model_class, topic_key in MODEL_TOPIC_MAP.items():
            if model_class in (Child, MedicationSchedule):
                continue  # handled separately

            order_field = MODEL_ORDER_FIELD.get(model_class, "-id")
            latest = (
                model_class.objects.filter(child=child).order_by(order_field).first()
            )
            payload = _serialize(model_class, latest, child) if latest else None
            mqtt_client.publish(
                f"{prefix}/{child.slug}/{topic_key}/state",
                json.dumps(payload, default=str),
            )

        # Medication schedules (list)
        _publish_medication_schedules(child, mqtt_client, prefix)

        # Stats
        _publish_stats(child)
