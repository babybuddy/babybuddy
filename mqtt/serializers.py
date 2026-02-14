# -*- coding: utf-8 -*-
"""Read-only ModelSerializer variants for MQTT payloads.

These serializers mirror the field lists from ``api/serializers.py`` but use
plain ``ModelSerializer`` (not ``HyperlinkedModelSerializer``) so they can be
instantiated without an HTTP request context.  Each serializer adds
``child_name`` and ``child_slug`` for convenience in MQTT consumers.
"""

from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer

from core import models

# ------------------------------------------------------------------
# Mixin – adds child_name / child_slug to payloads
# ------------------------------------------------------------------


class ChildInfoMixin(serializers.Serializer):
    """Adds ``child_name`` and ``child_slug`` derived from the FK."""

    child_name = serializers.SerializerMethodField()
    child_slug = serializers.SerializerMethodField()

    def get_child_name(self, obj):
        child = getattr(obj, "child", None)
        if child:
            return f"{child.first_name} {child.last_name}".strip()
        return None

    def get_child_slug(self, obj):
        child = getattr(obj, "child", None)
        return child.slug if child else None


class MqttTaggableSerializer(TaggitSerializer, serializers.ModelSerializer):
    tags = TagListSerializerField(required=False)


# ------------------------------------------------------------------
# Model serializers
# ------------------------------------------------------------------


class MqttBMISerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.BMI
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "bmi",
            "date",
            "notes",
            "tags",
        )


class MqttChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Child
        fields = ("id", "first_name", "last_name", "birth_date", "birth_time", "slug")


class MqttDiaperChangeSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.DiaperChange
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "time",
            "wet",
            "solid",
            "color",
            "amount",
            "notes",
            "tags",
        )


class MqttFeedingSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.Feeding
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "start",
            "end",
            "duration",
            "type",
            "method",
            "amount",
            "notes",
            "tags",
        )


class MqttHeadCircumferenceSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.HeadCircumference
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "head_circumference",
            "date",
            "notes",
            "tags",
        )


class MqttHeightSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.Height
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "height",
            "date",
            "notes",
            "tags",
        )


class MqttMedicationSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.Medication
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "medication_schedule",
            "name",
            "amount",
            "amount_unit",
            "time",
            "notes",
            "tags",
        )


class MqttMedicationScheduleSerializer(ChildInfoMixin, serializers.ModelSerializer):
    class Meta:
        model = models.MedicationSchedule
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "name",
            "amount",
            "amount_unit",
            "frequency",
            "schedule_time",
            "interval_hours",
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
            "active",
            "notes",
        )


class MqttNoteSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.Note
        fields = ("id", "child", "child_name", "child_slug", "note", "time", "tags")


class MqttPumpingSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.Pumping
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "amount",
            "start",
            "end",
            "duration",
            "notes",
            "tags",
        )


class MqttSleepSerializer(ChildInfoMixin, MqttTaggableSerializer):
    nap = serializers.BooleanField(allow_null=True, default=None, required=False)

    class Meta:
        model = models.Sleep
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "start",
            "end",
            "duration",
            "nap",
            "notes",
            "tags",
        )


class MqttTemperatureSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.Temperature
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "temperature",
            "time",
            "notes",
            "tags",
        )


class MqttTimerSerializer(ChildInfoMixin, serializers.ModelSerializer):
    duration = serializers.DurationField(read_only=True, required=False)

    class Meta:
        model = models.Timer
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "name",
            "start",
            "duration",
        )


class MqttTummyTimeSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.TummyTime
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "start",
            "end",
            "duration",
            "milestone",
            "tags",
        )


class MqttWeightSerializer(ChildInfoMixin, MqttTaggableSerializer):
    class Meta:
        model = models.Weight
        fields = (
            "id",
            "child",
            "child_name",
            "child_slug",
            "weight",
            "date",
            "notes",
            "tags",
        )
