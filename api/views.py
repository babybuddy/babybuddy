# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, views
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema

from core import models
from babybuddy import models as babybuddy_models
from mqtt.stats import compute_stats

from . import serializers, filters


class BMIViewSet(viewsets.ModelViewSet):
    queryset = models.BMI.objects.all()
    serializer_class = serializers.BMISerializer
    filterset_fields = ("child", "date")
    ordering_fields = ("child", "date")
    ordering = "-date"

    def get_view_name(self):
        """
        Gets the view name without changing the case of the model verbose name.
        """
        name = models.BMI._meta.verbose_name
        if self.suffix:
            name += " " + self.suffix
        return name


class ChildViewSet(viewsets.ModelViewSet):
    queryset = models.Child.objects.all()
    serializer_class = serializers.ChildSerializer
    lookup_field = "slug"
    filterset_fields = (
        "id",
        "first_name",
        "last_name",
        "slug",
        "birth_date",
        "birth_time",
    )
    ordering_fields = ("birth_date", "birth_time", "first_name", "last_name", "slug")
    ordering = ["-birth_date", "-birth_time"]

    @action(detail=True, methods=["get"])
    def stats(self, request, slug=None):
        """Return daily aggregate stats for a child, including overdue medications."""
        child = self.get_object()
        return Response(compute_stats(child))


class ExpirableViewSet(viewsets.ModelViewSet):
    queryset = models.Expirable.objects.all()
    serializer_class = serializers.ExpirableSerializer
    filterset_class = filters.ExpirableFilter
    ordering_fields = ("name", "time")
    ordering = "-time"

    @action(detail=True, methods=["post"])
    def discard(self, request, pk=None):
        """Toggle an Expirable's discarded status."""
        instance = self.get_object()
        instance.discarded = not instance.discarded
        instance.discarded_at = timezone.localtime() if instance.discarded else None
        instance.save()
        return Response(self.get_serializer(instance).data)


class DiaperChangeViewSet(viewsets.ModelViewSet):
    queryset = models.DiaperChange.objects.all()
    serializer_class = serializers.DiaperChangeSerializer
    filterset_class = filters.DiaperChangeFilter
    ordering_fields = ("amount", "time")
    ordering = "-time"


class FeedingViewSet(viewsets.ModelViewSet):
    queryset = models.Feeding.objects.all()
    serializer_class = serializers.FeedingSerializer
    filterset_class = filters.FeedingFilter
    ordering_fields = ("amount", "duration", "end", "start")
    ordering = "-end"


class HeadCircumferenceViewSet(viewsets.ModelViewSet):
    queryset = models.HeadCircumference.objects.all()
    serializer_class = serializers.HeadCircumferenceSerializer
    filterset_fields = ("child", "date")
    ordering_fields = ("date", "head_circumference")
    ordering = "-date"


class HeightViewSet(viewsets.ModelViewSet):
    queryset = models.Height.objects.all()
    serializer_class = serializers.HeightSerializer
    filterset_fields = ("child", "date")
    ordering_fields = ("date", "height")
    ordering = "-date"


class NoteViewSet(viewsets.ModelViewSet):
    queryset = models.Note.objects.all()
    serializer_class = serializers.NoteSerializer
    filterset_class = filters.NoteFilter
    ordering_fields = "time"
    ordering = "-time"


class PumpingViewSet(viewsets.ModelViewSet):
    queryset = models.Pumping.objects.all()
    serializer_class = serializers.PumpingSerializer
    filterset_class = filters.PumpingFilter
    ordering_fields = ("amount", "duration", "end", "start")
    ordering = "-end"


class SleepViewSet(viewsets.ModelViewSet):
    queryset = models.Sleep.objects.all()
    serializer_class = serializers.SleepSerializer
    filterset_class = filters.SleepFilter
    ordering_fields = ("duration", "end", "start")
    ordering = "-end"


class TagViewSet(viewsets.ModelViewSet):
    queryset = models.Tag.objects.all()
    serializer_class = serializers.TagSerializer
    lookup_field = "slug"
    filterset_fields = ("last_used", "name")
    ordering_fields = ("last_used", "name", "slug")
    ordering = "name"


class MedicationViewSet(viewsets.ModelViewSet):
    queryset = models.Medication.objects.all()
    serializer_class = serializers.MedicationSerializer
    filterset_class = filters.MedicationFilter
    ordering_fields = ("name", "time")
    ordering = "-time"


class MedicationScheduleViewSet(viewsets.ModelViewSet):
    queryset = models.MedicationSchedule.objects.all()
    serializer_class = serializers.MedicationScheduleSerializer
    filterset_fields = ("child", "active", "frequency")
    ordering_fields = ("name",)
    ordering = "name"


class TemperatureViewSet(viewsets.ModelViewSet):
    queryset = models.Temperature.objects.all()
    serializer_class = serializers.TemperatureSerializer
    filterset_class = filters.TemperatureFilter
    ordering_fields = ("temperature", "time")
    ordering = "-time"


class TimerViewSet(viewsets.ModelViewSet):
    queryset = models.Timer.objects.all()
    serializer_class = serializers.TimerSerializer
    filterset_class = filters.TimerFilter
    ordering_fields = ("duration", "end", "start")
    ordering = "-start"

    @action(detail=True, methods=["patch"])
    def restart(self, request, pk=None):
        timer = self.get_object()
        timer.restart()
        return Response(self.serializer_class(timer).data)


class TummyTimeViewSet(viewsets.ModelViewSet):
    queryset = models.TummyTime.objects.all()
    serializer_class = serializers.TummyTimeSerializer
    filterset_class = filters.TummyTimeFilter
    ordering_fields = ("duration", "end", "start")
    ordering = "-start"


class WeightViewSet(viewsets.ModelViewSet):
    queryset = models.Weight.objects.all()
    serializer_class = serializers.WeightSerializer
    filterset_fields = ("child", "date")
    ordering_fields = ("date", "weight")
    ordering = "-date"


class ProfileView(views.APIView):
    schema = AutoSchema(operation_id_base="CurrentProfile")

    action = "get"
    basename = "profile"

    queryset = babybuddy_models.Settings.objects.all()
    serializer_class = serializers.ProfileSerializer

    def get(self, request):
        settings = get_object_or_404(
            babybuddy_models.Settings.objects, user=request.user
        )
        serializer = self.serializer_class(settings)
        return Response(serializer.data)


def _get_choice_labels(model_class, field_name):
    """Return the display labels for a model choice field."""
    field = model_class._meta.get_field(field_name)
    return [str(label) for _value, label in field.choices]


class HADiscoveryView(views.APIView):
    """Metadata endpoint consumed by the Home Assistant integration.

    Returns a JSON object describing all entities, MQTT topics, and select
    options that Baby Buddy exposes.  This is a pure HTTP endpoint with zero
    dependency on the MQTT subsystem -- it works whether MQTT is enabled or not.
    """

    schema = AutoSchema(operation_id_base="HADiscovery")
    permission_classes = [IsAuthenticated]

    # -- static entity definitions (no mqtt imports) ----------------------

    MQTT_TOPICS = {
        "feeding": "feedings",
        "diaper_change": "changes",
        "sleep": "sleep",
        "pumping": "pumping",
        "tummy_time": "tummy-times",
        "temperature": "temperature",
        "weight": "weight",
        "height": "height",
        "head_circumference": "head-circumference",
        "bmi": "bmi",
        "note": "notes",
        "medication": "medications",
        "medication_schedule": "medication_schedules",
        "timer": "timers",
    }

    SENSORS = [
        {
            "key": "bmi",
            "name": "Last BMI",
            "state_key": "bmi",
            "state_class": "measurement",
            "icon": "mdi:human",
        },
        {
            "key": "changes",
            "name": "Last Diaper Change",
            "state_key": "time",
            "device_class": "timestamp",
            "icon": "mdi:paper-roll-outline",
        },
        {
            "key": "feedings",
            "name": "Last Feeding",
            "state_key": "start",
            "device_class": "timestamp",
            "icon": "mdi:baby-bottle-outline",
        },
        {
            "key": "head-circumference",
            "name": "Last Head Circumference",
            "state_key": "head_circumference",
            "state_class": "measurement",
            "icon": "mdi:tape-measure",
        },
        {
            "key": "height",
            "name": "Last Height",
            "state_key": "height",
            "state_class": "measurement",
            "icon": "mdi:human-male-height",
        },
        {
            "key": "medications",
            "name": "Last Medication",
            "state_key": "time",
            "device_class": "timestamp",
            "icon": "mdi:pill",
        },
        {
            "key": "notes",
            "name": "Last Note",
            "state_key": "time",
            "device_class": "timestamp",
            "icon": "mdi:note-text",
        },
        {
            "key": "pumping",
            "name": "Last Pumping",
            "state_key": "amount",
            "state_class": "measurement",
            "icon": "mdi:water-pump",
        },
        {
            "key": "sleep",
            "name": "Last Sleep",
            "state_key": "duration",
            "transform": "duration_to_minutes",
            "state_class": "measurement",
            "unit_of_measurement": "min",
            "icon": "mdi:sleep",
        },
        {
            "key": "temperature",
            "name": "Last Temperature",
            "state_key": "temperature",
            "device_class": "temperature",
            "state_class": "measurement",
            "icon": "mdi:thermometer",
        },
        {
            "key": "timers",
            "name": "Last Timer",
            "state_key": "start",
            "device_class": "timestamp",
            "icon": "mdi:timer-outline",
        },
        {
            "key": "tummy-times",
            "name": "Last Tummy Time",
            "state_key": "duration",
            "transform": "duration_to_minutes",
            "state_class": "measurement",
            "unit_of_measurement": "min",
            "icon": "mdi:human-child",
        },
        {
            "key": "weight",
            "name": "Last Weight",
            "state_key": "weight",
            "state_class": "measurement",
            "icon": "mdi:scale-bathroom",
        },
    ]

    STATS_SENSORS = [
        {
            "key": "feedings_today",
            "name": "Feedings Today",
            "stats_field": "feedings_today",
            "state_class": "measurement",
            "icon": "mdi:counter",
        },
        {
            "key": "diaper_changes_today",
            "name": "Diaper Changes Today",
            "stats_field": "diaper_changes_today",
            "state_class": "measurement",
            "icon": "mdi:counter",
        },
        {
            "key": "sleep_total_today_minutes",
            "name": "Sleep Total Today",
            "stats_field": "sleep_total_today_minutes",
            "state_class": "measurement",
            "unit_of_measurement": "min",
            "icon": "mdi:sleep",
        },
        {
            "key": "last_feeding_minutes_ago",
            "name": "Minutes Since Last Feeding",
            "stats_field": "last_feeding_minutes_ago",
            "unit_of_measurement": "min",
            "icon": "mdi:clock-outline",
        },
        {
            "key": "last_diaper_change_minutes_ago",
            "name": "Minutes Since Last Diaper Change",
            "stats_field": "last_diaper_change_minutes_ago",
            "unit_of_measurement": "min",
            "icon": "mdi:clock-outline",
        },
        {
            "key": "medications_overdue_count",
            "name": "Medications Overdue",
            "stats_field": "medications_overdue_count",
            "state_class": "measurement",
            "icon": "mdi:pill",
        },
    ]

    BINARY_SENSORS = [
        {
            "key": "medication_overdue",
            "name": "Medication Overdue",
            "device_class": "problem",
            "stats_field": "medications_overdue_count",
            "condition": "greater_than_zero",
            "attributes": {
                "overdue_names": "medications_overdue",
                "overdue_count": "medications_overdue_count",
            },
        },
    ]

    def get(self, request):
        data = {
            "version": 1,
            "stats_endpoint": "/api/children/{slug}/stats/",
            "mqtt": {
                "default_topic_prefix": "babybuddy",
                "topics": self.MQTT_TOPICS,
            },
            "sensors": self.SENSORS,
            "stats_sensors": self.STATS_SENSORS,
            "binary_sensors": self.BINARY_SENSORS,
            "selects": [
                {
                    "key": "diaper_color",
                    "name": "Diaper Color",
                    "icon": "mdi:paper-roll-outline",
                    "options": _get_choice_labels(models.DiaperChange, "color"),
                },
                {
                    "key": "change_type",
                    "name": "Change Type",
                    "icon": "mdi:paper-roll-outline",
                    "options": ["Wet", "Solid", "Wet and Solid"],
                },
                {
                    "key": "feeding_method",
                    "name": "Feeding Method",
                    "icon": "mdi:baby-bottle-outline",
                    "options": _get_choice_labels(models.Feeding, "method"),
                },
                {
                    "key": "feeding_type",
                    "name": "Feeding Type",
                    "icon": "mdi:baby-bottle-outline",
                    "options": _get_choice_labels(models.Feeding, "type"),
                },
            ],
        }
        return Response(data)
