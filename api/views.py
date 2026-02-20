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

    TRANSFORMS = {
        "diaper_type_to_booleans": {
            "type": "mapping",
            "removes_field": True,
            "mapping": {
                "Wet": {"wet": True, "solid": False},
                "Solid": {"wet": False, "solid": True},
                "Wet and Solid": {"wet": True, "solid": True},
            },
        },
        "lowercase": {
            "type": "value_transform",
            "operation": "lowercase",
        },
    }

    API_META = {
        "list_response_format": {
            "count_field": "count",
            "results_field": "results",
        },
        "child_filter_param": "child",
        "limit_param": "limit",
        "stats_endpoint": "/api/children/{slug}/stats/",
    }

    CHILD_META = {
        "icon": "mdi:baby-face-outline",
        "device_class": "babybuddy_child",
        "name_template": "{first_name} {last_name}",
        "state_field": "birth_date",
        "picture_field": "picture",
        "dashboard_path": "/children/{slug}/dashboard/",
        "fields": [
            "id",
            "first_name",
            "last_name",
            "slug",
            "birth_date",
            "picture",
        ],
    }

    TIMER_META = {
        "endpoint": "timers",
        "name": "Timer",
        "icon": "mdi:timer-sand",
        "start_fields": {"child": "child_id", "start": "datetime"},
        "active_detection": "presence",
        "id_field": "id",
    }

    SERVICES = [
        {
            "key": "add_child",
            "endpoint": "children",
            "name": "Add Child",
            "description": "Add a new child to Baby Buddy",
            "uses_timer": False,
            "common_fields": False,
            "fields": {
                "birth_date": {
                    "type": "date",
                    "required": True,
                    "default": "today",
                    "name": "Birth Date",
                    "description": "Child's date of birth",
                },
                "first_name": {
                    "type": "string",
                    "required": True,
                    "name": "First Name",
                    "description": "Child's first name",
                },
                "last_name": {
                    "type": "string",
                    "required": True,
                    "name": "Last Name",
                    "description": "Child's last name",
                },
            },
        },
        {
            "key": "add_bmi",
            "endpoint": "bmi",
            "name": "Add BMI",
            "description": "Record a BMI measurement",
            "uses_timer": False,
            "common_fields": True,
            "fields": {
                "bmi": {
                    "type": "float",
                    "required": True,
                    "name": "BMI",
                    "description": "Body mass index value",
                    "selector_hints": {"min": 0.1, "max": 100.0, "step": 0.1},
                },
                "date": {
                    "type": "date",
                    "required": False,
                    "name": "Date",
                    "description": "Date of measurement",
                },
            },
        },
        {
            "key": "add_diaper_change",
            "endpoint": "changes",
            "name": "Add Diaper Change",
            "description": "Record a diaper change",
            "uses_timer": False,
            "common_fields": True,
            "fields": {
                "time": {
                    "type": "datetime",
                    "required": False,
                    "name": "Time",
                    "description": "Date and time of the diaper change",
                },
                "type": {
                    "type": "select",
                    "select_key": "change_type",
                    "required": False,
                    "name": "Type",
                    "description": "Diaper change type",
                },
                "color": {
                    "type": "select",
                    "select_key": "diaper_color",
                    "required": False,
                    "name": "Color",
                    "description": "Diaper contents color",
                },
                "amount": {
                    "type": "float",
                    "required": False,
                    "name": "Amount",
                    "description": "Amount of diaper contents",
                    "selector_hints": {"min": 0.0, "max": 500.0, "step": 0.1},
                },
            },
            "transforms": {
                "type": "diaper_type_to_booleans",
                "color": "lowercase",
            },
        },
        {
            "key": "add_feeding",
            "endpoint": "feedings",
            "name": "Add Feeding",
            "description": "Record a feeding",
            "uses_timer": True,
            "common_fields": True,
            "fields": {
                "type": {
                    "type": "select",
                    "select_key": "feeding_type",
                    "required": True,
                    "name": "Type",
                    "description": "Type of feeding",
                },
                "method": {
                    "type": "select",
                    "select_key": "feeding_method",
                    "required": True,
                    "name": "Method",
                    "description": "Feeding method",
                },
                "amount": {
                    "type": "float",
                    "required": False,
                    "name": "Amount",
                    "description": "Amount consumed",
                    "selector_hints": {"min": 0.0, "max": 500.0, "step": 0.1},
                },
                "notes": {
                    "type": "string",
                    "required": False,
                    "name": "Notes",
                    "description": "Additional notes",
                    "multiline": True,
                },
            },
            "transforms": {
                "type": "lowercase",
                "method": "lowercase",
            },
        },
        {
            "key": "add_head_circumference",
            "endpoint": "head-circumference",
            "name": "Add Head Circumference",
            "description": "Record a head circumference measurement",
            "uses_timer": False,
            "common_fields": True,
            "fields": {
                "head_circumference": {
                    "type": "float",
                    "required": True,
                    "name": "Head Circumference",
                    "description": "Head circumference measurement",
                    "selector_hints": {"min": 0.1, "step": 0.1},
                },
                "date": {
                    "type": "date",
                    "required": False,
                    "name": "Date",
                    "description": "Date of measurement",
                },
            },
        },
        {
            "key": "add_height",
            "endpoint": "height",
            "name": "Add Height",
            "description": "Record a height measurement",
            "uses_timer": False,
            "common_fields": True,
            "fields": {
                "height": {
                    "type": "float",
                    "required": True,
                    "name": "Height",
                    "description": "Height measurement",
                    "selector_hints": {"min": 0.1, "step": 0.1},
                },
                "date": {
                    "type": "date",
                    "required": False,
                    "name": "Date",
                    "description": "Date of measurement",
                },
            },
        },
        {
            "key": "add_note",
            "endpoint": "notes",
            "name": "Add Note",
            "description": "Add a note for a child",
            "uses_timer": False,
            "common_fields": False,
            "fields": {
                "child": {
                    "type": "entity_id",
                    "required": True,
                    "name": "Child",
                    "description": "Child to add the note for",
                    "entity_domain": "sensor",
                },
                "note": {
                    "type": "string",
                    "required": True,
                    "name": "Note",
                    "description": "Note text",
                    "multiline": True,
                },
                "time": {
                    "type": "datetime",
                    "required": False,
                    "name": "Time",
                    "description": "Date and time of the note",
                },
                "tags": {
                    "type": "string_list",
                    "required": False,
                    "name": "Tags",
                    "description": "Tags to associate with the note",
                },
            },
        },
        {
            "key": "add_pumping",
            "endpoint": "pumping",
            "name": "Add Pumping",
            "description": "Record a pumping session",
            "uses_timer": True,
            "common_fields": True,
            "fields": {
                "amount": {
                    "type": "float",
                    "required": False,
                    "name": "Amount",
                    "description": "Amount pumped",
                    "selector_hints": {"min": 0.0, "max": 500.0, "step": 0.1},
                },
                "notes": {
                    "type": "string",
                    "required": False,
                    "name": "Notes",
                    "description": "Additional notes",
                    "multiline": True,
                },
            },
        },
        {
            "key": "add_sleep",
            "endpoint": "sleep",
            "name": "Add Sleep",
            "description": "Record a sleep session",
            "uses_timer": True,
            "common_fields": True,
            "fields": {
                "nap": {
                    "type": "boolean",
                    "required": False,
                    "name": "Nap",
                    "description": "Was this a nap (not overnight sleep)?",
                },
                "notes": {
                    "type": "string",
                    "required": False,
                    "name": "Notes",
                    "description": "Additional notes",
                    "multiline": True,
                },
            },
        },
        {
            "key": "add_temperature",
            "endpoint": "temperature",
            "name": "Add Temperature",
            "description": "Record a temperature measurement",
            "uses_timer": False,
            "common_fields": True,
            "fields": {
                "temperature": {
                    "type": "float",
                    "required": True,
                    "name": "Temperature",
                    "description": "Temperature reading",
                    "selector_hints": {"min": 35.0, "max": 150.0, "step": 0.1},
                },
                "time": {
                    "type": "datetime",
                    "required": False,
                    "name": "Time",
                    "description": "Date and time of the reading",
                },
            },
        },
        {
            "key": "add_tummy_time",
            "endpoint": "tummy-times",
            "name": "Add Tummy Time",
            "description": "Record a tummy time session",
            "uses_timer": True,
            "common_fields": True,
            "fields": {
                "milestone": {
                    "type": "string",
                    "required": False,
                    "name": "Milestone",
                    "description": "Milestone achieved during tummy time",
                    "multiline": True,
                },
            },
        },
        {
            "key": "add_weight",
            "endpoint": "weight",
            "name": "Add Weight",
            "description": "Record a weight measurement",
            "uses_timer": False,
            "common_fields": True,
            "fields": {
                "weight": {
                    "type": "float",
                    "required": True,
                    "name": "Weight",
                    "description": "Weight measurement",
                    "selector_hints": {"min": 0.1, "step": 0.1},
                },
                "date": {
                    "type": "date",
                    "required": False,
                    "name": "Date",
                    "description": "Date of measurement",
                },
            },
        },
        {
            "key": "add_medication",
            "endpoint": "medications",
            "name": "Add Medication",
            "description": "Record a medication entry",
            "uses_timer": False,
            "common_fields": True,
            "fields": {
                "name": {
                    "type": "string",
                    "required": True,
                    "name": "Medication Name",
                    "description": "Name of the medication",
                },
                "amount": {
                    "type": "float",
                    "required": True,
                    "name": "Amount",
                    "description": "Medication dosage amount",
                    "selector_hints": {"min": 0.0, "max": 500.0, "step": 0.1},
                },
                "amount_unit": {
                    "type": "select",
                    "select_key": "medication_units",
                    "required": True,
                    "name": "Amount Unit",
                    "description": "Unit for the dosage amount",
                },
                "time": {
                    "type": "datetime",
                    "required": False,
                    "name": "Time",
                    "description": "Date and time the medication was given",
                },
            },
        },
        {
            "key": "give_medication",
            "endpoint": "medications",
            "name": "Give Scheduled Medication",
            "description": "Give a medication from an existing schedule",
            "uses_timer": False,
            "common_fields": False,
            "fields": {
                "child": {
                    "type": "entity_id",
                    "required": True,
                    "name": "Child",
                    "description": "Child to give medication to",
                    "entity_domain": "sensor",
                },
                "schedule_id": {
                    "type": "int",
                    "required": True,
                    "name": "Schedule ID",
                    "description": "Medication schedule to give from",
                    "selector_hints": {"min": 1},
                },
                "name": {
                    "type": "string",
                    "required": True,
                    "name": "Medication Name",
                    "description": "Name of the medication",
                },
                "amount": {
                    "type": "float",
                    "required": True,
                    "name": "Amount",
                    "description": "Medication dosage amount",
                    "selector_hints": {"min": 0.0, "max": 500.0, "step": 0.1},
                },
                "amount_unit": {
                    "type": "select",
                    "select_key": "medication_units",
                    "required": True,
                    "name": "Amount Unit",
                    "description": "Unit for the dosage amount",
                },
            },
            "extra_data": {
                "medication_schedule": {"from_field": "schedule_id"},
            },
        },
        {
            "key": "delete_last_entry",
            "endpoint": None,
            "name": "Delete Last Entry",
            "description": "Delete the last entry for a sensor",
            "method": "DELETE",
            "uses_timer": False,
            "common_fields": False,
            "fields": {
                "entity_id": {
                    "type": "entity_id",
                    "required": True,
                    "name": "Entity",
                    "description": "Baby Buddy sensor entity to delete from",
                    "entity_domain": "sensor",
                },
            },
        },
        {
            "key": "start_timer",
            "endpoint": "timers",
            "name": "Start Timer",
            "description": "Start a new timer for a child",
            "uses_timer": False,
            "common_fields": False,
            "fields": {
                "child": {
                    "type": "entity_id",
                    "required": True,
                    "name": "Child",
                    "description": "Child to start the timer for",
                    "entity_domain": "switch",
                },
                "start": {
                    "type": "datetime",
                    "required": False,
                    "name": "Start Time",
                    "description": "Timer start time (defaults to now)",
                },
                "name": {
                    "type": "string",
                    "required": False,
                    "name": "Timer Name",
                    "description": "Optional name for the timer",
                },
            },
        },
    ]

    def get(self, request):
        from babybuddy import VERSION
        from mqtt.utils import get_mqtt_ha_settings

        data = {
            "version": 2,
            "babybuddy_version": VERSION,
            "settings": {
                "mqtt_discovery_enabled": bool(get_mqtt_ha_settings().ha_discovery),
            },
            "api": self.API_META,
            "child": self.CHILD_META,
            "timer": self.TIMER_META,
            "transforms": self.TRANSFORMS,
            "mqtt": {
                "default_topic_prefix": "babybuddy",
                "topic_pattern": "{prefix}/{child_slug}/{data_type}/state",
                "stats_topic_pattern": "{prefix}/{child_slug}/stats/state",
                "topics": self.MQTT_TOPICS,
            },
            "sensors": self.SENSORS,
            "stats_sensors": self.STATS_SENSORS,
            "binary_sensors": self.BINARY_SENSORS,
            "selects": [
                {
                    "key": "diaper_color",
                    "name": "Diaper Color",
                    "icon": "mdi:palette",
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
                {
                    "key": "medication_units",
                    "name": "Medication Unit",
                    "icon": "mdi:pill",
                    "options": _get_choice_labels(
                        models.MedicationSchedule, "amount_unit"
                    ),
                    "entity": False,
                },
            ],
            "services": self.SERVICES,
        }
        return Response(data)


class HASettingsView(views.APIView):
    """Read and update Home Assistant-related settings."""

    schema = AutoSchema(operation_id_base="HASettings")
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _get_settings():
        from mqtt.utils import get_mqtt_ha_settings

        return {"mqtt_discovery_enabled": bool(get_mqtt_ha_settings().ha_discovery)}

    def get(self, request):
        return Response(self._get_settings())

    def patch(self, request):
        from mqtt.utils import get_mqtt_ha_settings
        from mqtt.discovery import remove_all_discovery

        s = get_mqtt_ha_settings()
        if "mqtt_discovery_enabled" in request.data:
            new_val = bool(request.data["mqtt_discovery_enabled"])
            old_val = bool(s.ha_discovery)
            if new_val != old_val:
                s.ha_discovery = new_val
                if not new_val:
                    remove_all_discovery()

        return Response(self._get_settings())


class MQTTDiscoverView(views.APIView):
    """Scan the network for reachable MQTT brokers via mDNS and well-known
    hostnames. Returns a JSON list of discovered brokers."""

    schema = AutoSchema(operation_id_base="MQTTDiscover")
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from mqtt.discover import discover_brokers

        return Response(discover_brokers())
