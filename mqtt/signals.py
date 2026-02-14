# -*- coding: utf-8 -*-
"""Connect Django signals for MQTT publishing.

Importing this module (done in ``MqttConfig.ready()``) wires up
``post_save`` and ``post_delete`` for every tracked core model.
"""

from django.db.models.signals import post_delete, post_save

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

from .publisher import on_model_delete, on_model_save

TRACKED_MODELS = [
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
]

for _model in TRACKED_MODELS:
    post_save.connect(
        on_model_save, sender=_model, dispatch_uid=f"mqtt_save_{_model.__name__}"
    )
    post_delete.connect(
        on_model_delete, sender=_model, dispatch_uid=f"mqtt_delete_{_model.__name__}"
    )
