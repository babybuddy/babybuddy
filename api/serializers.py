# -*- coding: utf-8 -*-
from copy import deepcopy
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.contrib.auth import get_user_model
from django.utils import timezone

from taggit.serializers import TagListSerializerField, TaggitSerializer

from core import models
from babybuddy import models as babybuddy_models


class CoreModelSerializer(serializers.HyperlinkedModelSerializer):
    """
    Provide the child link (used by most core models) and run model clean()
    methods during POST operations.
    """

    child = serializers.PrimaryKeyRelatedField(queryset=models.Child.objects.all())

    def validate(self, attrs):
        # Ensure that all instance data is available for partial updates to
        # support clean methods that compare multiple fields.
        if self.partial:
            new_instance = deepcopy(self.instance)
            for attr, value in attrs.items():
                setattr(new_instance, attr, value)
        else:
            new_instance = self.Meta.model(**attrs)
        new_instance.clean()
        return attrs


class CoreModelWithDurationSerializer(CoreModelSerializer):
    """
    Specific serializer base for models with a "start" and "end" field.
    """

    child = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        help_text="Required unless a Timer value is provided.",
        queryset=models.Child.objects.all(),
        required=False,
    )

    timer = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        help_text="May be used in place of the Start, End, and/or Child values.",
        queryset=models.Timer.objects.all(),
        required=False,
        write_only=True,
    )

    class Meta:
        abstract = True
        extra_kwargs = {
            "start": {
                "help_text": "Required unless a Timer value is provided.",
                "required": False,
            },
            "end": {
                "help_text": "Required unless a Timer value is provided.",
                "required": False,
            },
        }

    def validate(self, attrs):
        # Check for a special "timer" data argument that can be used in place
        # of "start" and "end" fields as well as "child" if it is set on the
        # Timer entry.
        timer = None
        if "timer" in attrs:
            # Remove the "timer" attribute (super validation would fail as it
            # is not a true field on the model).
            timer = attrs["timer"]
            attrs.pop("timer")

            if timer.child:
                attrs["child"] = timer.child

            # Overwrites values provided directly!
            attrs["start"] = timer.start
            attrs["end"] = timezone.now()

        # The "child", "start", and "end" field should all be set at this
        # point. If one is not, model validation will fail because they are
        # required fields at the model level.
        if not self.partial:
            errors = {}
            for field in ["child", "start", "end"]:
                if field not in attrs or not attrs[field]:
                    errors[field] = "This field is required."
            if len(errors) > 0:
                raise ValidationError(errors)

        attrs = super().validate(attrs)

        # Only actually stop the timer if all validation passed.
        if timer:
            timer.stop()

        return attrs


class TaggableSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    tags = TagListSerializerField(required=False)


class BMISerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.BMI
        fields = ("id", "child", "bmi", "date", "notes", "tags")
        extra_kwargs = {
            "core.BMI.bmi": {"label": "BMI"},
        }


class PumpingSerializer(CoreModelWithDurationSerializer, TaggableSerializer):
    class Meta(CoreModelWithDurationSerializer.Meta):
        model = models.Pumping
        fields = (
            "id",
            "child",
            "amount",
            "amount_unit",
            "amount_normalized",
            "method",
            "start",
            "end",
            "duration",
            "notes",
            "tags",
            "timer",
        )


class ChildSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Child
        fields = (
            "id",
            "first_name",
            "last_name",
            "birth_date",
            "birth_time",
            "slug",
            "picture",
        )
        lookup_field = "slug"


class DiaperChangeSerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.DiaperChange
        fields = (
            "id",
            "child",
            "time",
            "wet",
            "solid",
            "color",
            "amount",
            "wet_amount",
            "solid_amount",
            "blowout",
            "blowout_direction",
            "diaper_size",
            "diaper_brand",
            "notes",
            "tags",
        )


class FeedingSerializer(CoreModelWithDurationSerializer, TaggableSerializer):
    # HyperlinkedModelSerializer would auto-generate a HyperlinkedRelatedField
    # for this self-FK, reversing the bare name "feeding-detail" — which fails
    # because api urls are namespaced (api:feeding-detail). Explicit PK field.
    previous_feeding = serializers.PrimaryKeyRelatedField(
        queryset=models.Feeding.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta(CoreModelWithDurationSerializer.Meta):
        model = models.Feeding
        fields = (
            "id",
            "child",
            "start",
            "end",
            "timer",
            "duration",
            "type",
            "method",
            "amount",
            "amount_unit",
            "amount_normalized",
            "breastfeeding_modifier",
            "sns_amount",
            "sns_milk_type",
            "nipple_size",
            "formula_brand",
            "bottle_brand",
            "bottle_model",
            "previous_feeding",
            "amount_mixed",
            "notes",
            "tags",
        )


class HeadCircumferenceSerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.HeadCircumference
        fields = ("id", "child", "head_circumference", "date", "notes", "tags")


class HeightSerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.Height
        fields = ("id", "child", "height", "date", "notes", "tags")


class MedicationSerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.Medication
        fields = (
            "id",
            "child",
            "name",
            "dosage",
            "dosage_unit",
            "time",
            "next_dose_interval",
            "doctor_visit",
            "notes",
            "tags",
        )


class NoteSerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.Note
        fields = ("id", "child", "note", "image", "time", "tags")


class SleepSerializer(CoreModelWithDurationSerializer, TaggableSerializer):
    nap = serializers.BooleanField(allow_null=True, default=None, required=False)

    class Meta(CoreModelWithDurationSerializer.Meta):
        model = models.Sleep
        fields = (
            "id",
            "child",
            "start",
            "end",
            "timer",
            "duration",
            "nap",
            "notes",
            "tags",
        )


class TagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = models.Tag
        fields = ("slug", "name", "color", "last_used")
        extra_kwargs = {
            "slug": {"required": False, "read_only": True},
            "color": {"required": False},
            "last_used": {"required": False, "read_only": True},
        }


class TemperatureSerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.Temperature
        fields = ("id", "child", "temperature", "time", "notes", "tags")


class TimerSerializer(CoreModelSerializer):
    child = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        allow_empty=True,
        queryset=models.Child.objects.all(),
        required=False,
    )
    user = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        allow_empty=True,
        queryset=get_user_model().objects.all(),
        required=False,
    )
    duration = serializers.DurationField(read_only=True, required=False)

    class Meta:
        model = models.Timer
        fields = ("id", "child", "name", "start", "duration", "user")

    def validate(self, attrs):
        attrs = super(TimerSerializer, self).validate(attrs)

        # Set user to current user if no value is provided.
        if "user" not in attrs or attrs["user"] is None:
            attrs["user"] = self.context["request"].user

        return attrs


class TummyTimeSerializer(CoreModelWithDurationSerializer, TaggableSerializer):
    class Meta(CoreModelWithDurationSerializer.Meta):
        model = models.TummyTime
        fields = (
            "id",
            "child",
            "start",
            "end",
            "timer",
            "duration",
            "milestone",
            "tags",
        )


class WeightSerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.Weight
        fields = ("id", "child", "weight", "date", "notes", "tags")


class FeedInventorySerializer(CoreModelSerializer, TaggableSerializer):
    child = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        queryset=models.Child.objects.all(),
        required=False,
        help_text="Optional. Leave blank for household milk pool.",
    )
    pumping_session = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        queryset=models.Pumping.objects.all(),
        required=False,
    )

    class Meta:
        model = models.FeedInventory
        fields = (
            "id",
            "child",
            "pumping_session",
            "type",
            "amount",
            "amount_unit",
            "amount_normalized",
            "amount_remaining",
            "storage_location",
            "status",
            "expressed_at",
            "fridge_entered_at",
            "freezer_entered_at",
            "thaw_started_at",
            "thaw_completed_at",
            "warmed_at",
            "room_temp_since",
            "cooler_entered_at",
            "notes",
            "tags",
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
        )
        extra_kwargs = {k: {"read_only": True} for k in fields}


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)
    api_key = serializers.SerializerMethodField("get_api_key")

    def get_api_key(self, value):
        return self.instance.api_key().key

    class Meta:
        model = babybuddy_models.Settings
        fields = (
            "user",
            "language",
            "timezone",
            "api_key",
        )
        extra_kwargs = {k: {"read_only": True} for k in fields}


class ProductLineSerializer(CoreModelSerializer):
    class Meta:
        model = models.ProductLine
        fields = (
            "id",
            "item_type",
            "brand",
            "line",
        )


class SupplyItemSerializer(CoreModelSerializer):
    product_line = serializers.PrimaryKeyRelatedField(queryset=models.ProductLine.objects.all())

    class Meta:
        model = models.SupplyItem
        fields = (
            "id",
            "child",
            "product_line",
            "size",
            "quantity",
            "purchase_date",
            "notes",
        )


class SpitUpSerializer(CoreModelSerializer):
    # Same namespaced-reverse issue as previous_feeding — explicit PK field.
    related_feeding = serializers.PrimaryKeyRelatedField(
        queryset=models.Feeding.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = models.SpitUp
        fields = (
            "id",
            "child",
            "time",
            "amount",
            "appearance",
            "related_feeding",
            "notes",
        )


class EquipmentItemSerializer(CoreModelSerializer):
    # Same namespaced-reverse issue — explicit PK field (pattern from
    # SupplyItemSerializer.product_line).
    product_line = serializers.PrimaryKeyRelatedField(
        queryset=models.ProductLine.objects.all(),
    )

    class Meta:
        model = models.EquipmentItem
        fields = (
            "id", "child", "product_line", "size", "quantity",
            "acquired_date", "source", "disposal_status", "disposal_date", "notes",
        )


class FeedInventorySerializer(CoreModelSerializer, TaggableSerializer):
    child = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        queryset=models.Child.objects.all(),
        required=False,
        help_text="Optional. Leave blank for household milk pool.",
    )
    pumping_session = serializers.PrimaryKeyRelatedField(
        allow_null=True,
        queryset=models.Pumping.objects.all(),
        required=False,
    )

    class Meta:
        model = models.FeedInventory
        fields = (
            "id",
            "child",
            "pumping_session",
            "type",
            "amount",
            "amount_unit",
            "amount_normalized",
            "amount_remaining",
            "storage_location",
            "status",
            "expressed_at",
            "fridge_entered_at",
            "freezer_entered_at",
            "thaw_started_at",
            "thaw_completed_at",
            "warmed_at",
            "room_temp_since",
            "cooler_entered_at",
            "notes",
            "tags",
        )


class DoctorVisitSerializer(CoreModelSerializer):
    class Meta:
        model = models.DoctorVisit
        fields = (
            "id", "child", "date_time", "appointment_type",
            "doctor_name", "practice", "reason", "symptoms_notes",
            "diagnosis", "action_items", "weight_measured", "notes",
        )


class FormulaStockSerializer(CoreModelSerializer):
    product_line = serializers.PrimaryKeyRelatedField(queryset=models.ProductLine.objects.all())

    class Meta:
        model = models.FormulaStock
        fields = (
            "id",
            "product_line",
            "form",
            "container_size",
            "quantity",
            "expiry_date",
            "opened_at",
            "grams_remaining",
            "ml_remaining",
            "usage_eligible",
            "drain_priority",
            "is_reserve",
            "notes",
        )


class PreparedFeedSerializer(CoreModelSerializer):
    source_pool = serializers.PrimaryKeyRelatedField(
        queryset=models.FormulaStock.objects.all(), allow_null=True, required=False
    )
    source_inventory = serializers.PrimaryKeyRelatedField(
        queryset=models.FeedInventory.objects.all(), allow_null=True, required=False
    )

    class Meta:
        model = models.PreparedFeed
        fields = (
            "id",
            "source_pool",
            "source_inventory",
            "prepared_from",
            "amount",
            "amount_remaining",
            "grams_used",
            "prepared_at",
            "fridge_entered_at",
            "first_fed_at",
            "status",
            "notes",
        )

