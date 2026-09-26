# -*- coding: utf-8 -*-
import secrets
from copy import deepcopy
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
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
            timer = attrs.pop("timer")
            if timer is None:
                raise ValidationError({"timer": "This field may not be null."})
            if not timer.can_be_consumed_by(self.context["request"].user):
                raise PermissionDenied("You do not have permission to consume timers.")

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

        self.timer = timer
        return attrs

    @transaction.atomic
    def save(self, **kwargs):
        timer = getattr(self, "timer", None)
        if timer is not None:
            try:
                timer = models.Timer.objects.select_for_update().get(pk=timer.pk)
            except models.Timer.DoesNotExist:
                raise ValidationError({"timer": "This timer no longer exists."})
            # The timer may have changed owner since validation.
            if not timer.can_be_consumed_by(self.context["request"].user):
                raise PermissionDenied("You do not have permission to consume timers.")
        instance = super().save(**kwargs)
        if timer is not None:
            timer.stop()
        return instance


class TaggableSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    tags = TagListSerializerField(required=False)

    def validate_tags(self, tags):
        current = self.instance.tags.names() if self.instance else ()
        models.Tag.check_assignment_permissions(
            self.context["request"].user, tags, current
        )
        return tags


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
            "due_date",
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
            "notes",
            "tags",
        )


class FeedingSerializer(CoreModelWithDurationSerializer, TaggableSerializer):
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
        request_user = self.context["request"].user

        if self.instance is None:
            # Set user to current user if no value is provided.
            if "user" not in attrs or attrs["user"] is None:
                attrs["user"] = request_user
        elif "user" in attrs:
            # The owner may consume the timer, so taking over another user's
            # timer requires the same permission as consuming it.
            attrs["user"] = attrs["user"] or request_user
            if attrs["user"] != self.instance.user and not request_user.has_perm(
                "core.delete_timer"
            ):
                raise PermissionDenied(
                    "You do not have permission to change the user of a timer."
                )

        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        # Work on the stored timer, whose owner may have changed since
        # validation, so the check uses it and a stale owner is never saved back.
        instance = models.Timer.objects.select_for_update().get(pk=instance.pk)
        user = validated_data.get("user", instance.user)
        if user != instance.user and not self.context["request"].user.has_perm(
            "core.delete_timer"
        ):
            raise PermissionDenied(
                "You do not have permission to change the user of a timer."
            )
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


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
            "notes",
            "tags",
        )


class WeightSerializer(CoreModelSerializer, TaggableSerializer):
    class Meta:
        model = models.Weight
        fields = ("id", "child", "weight", "date", "notes", "tags")


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


class CaregiverSerializer(serializers.ModelSerializer):
    """
    A caregiver account, created and managed without the admin area.

    Only the fields a caregiver account needs are here. The role cannot be
    changed through them: there is no staff or superuser flag and no groups
    field, so an account made here stays a caregiver whatever is sent later.

    The account is used through its API key, which is returned once, when the
    account is created. It has no password unless an email address is given,
    in which case it is created with one nobody knows so that the reset flow
    can reach it and its owner can set a real one.
    """

    access_expires = serializers.DateTimeField(
        source="settings.access_expires", required=False, allow_null=True
    )

    class Meta:
        model = get_user_model()
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "is_active",
            "access_expires",
        )

    def create(self, validated_data):
        expires = validated_data.pop("settings", {}).get("access_expires")
        # Django's reset form skips accounts whose password is unusable, so an
        # address on its own would never receive anything. With one the account
        # gets a usable password that nobody knows; without one it gets none.
        password = secrets.token_urlsafe(32) if validated_data.get("email") else None
        with transaction.atomic():
            user = get_user_model().objects.create_user(
                password=password, **validated_data
            )
            user.groups.add(
                Group.objects.get(name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"])
            )
            user.settings.access_expires = expires
            user.settings.save()
        return user

    def update(self, instance, validated_data):
        user_settings = validated_data.pop("settings", {})
        with transaction.atomic():
            user = super().update(instance, validated_data)
            if user.email and not user.has_usable_password():
                # The address is what the reset flow needs, so an account that
                # gains one has to gain a usable password with it.
                user.set_password(secrets.token_urlsafe(32))
                user.save(update_fields=["password"])
            if "access_expires" in user_settings:
                user.settings.access_expires = user_settings["access_expires"]
                user.settings.save()
        return user
