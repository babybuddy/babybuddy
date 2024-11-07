# -*- coding: utf-8 -*-
import datetime
import json
import re

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.text import format_lazy, slugify
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager as TaggitTaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

from babybuddy.site_settings import NapSettings
from core.utils import random_color, timezone_aware_duration


def validate_date(date, field_name):
    """
    Confirm that a date is not in the future.
    :param date: a timezone aware date instance.
    :param field_name: the name of the field being checked.
    :return:
    """
    if date and date > timezone.localdate():
        raise ValidationError(
            {field_name: _("Date can not be in the future.")}, code="date_invalid"
        )


def validate_duration(model, max_duration=datetime.timedelta(hours=24)):
    """
    Basic sanity checks for models with a duration
    :param model: a model instance with 'start' and 'end' attributes
    :param max_duration: maximum allowed duration between start and end time
    :return:
    """
    if model.start and model.end:
        # Compare and calculate in UTC to account for DST changes between dates.
        start = model.start.astimezone(datetime.timezone.utc)
        end = model.end.astimezone(datetime.timezone.utc)
        if start > end:
            raise ValidationError(
                _("Start time must come before end time."), code="end_before_start"
            )
        if end - start > max_duration:
            raise ValidationError(_("Duration too long."), code="max_duration")


def validate_unique_period(queryset, model):
    """
    Confirm that model's start and end date do not intersect with other
    instances.
    :param queryset: a queryset of instances to check against.
    :param model: a model instance with 'start' and 'end' attributes
    :return:
    """
    if model.id:
        queryset = queryset.exclude(id=model.id)
    if model.start and model.end:
        if queryset.filter(start__lt=model.end, end__gt=model.start):
            raise ValidationError(
                _("Another entry intersects the specified time period."),
                code="period_intersection",
            )


def validate_time(time, field_name):
    """
    Confirm that a time is not in the future.
    :param time: a timezone aware datetime instance.
    :param field_name: the name of the field being checked.
    :return:
    """
    if time and time > timezone.localtime():
        raise ValidationError(
            {field_name: _("Date/time can not be in the future.")}, code="time_invalid"
        )


class Tag(TagBase):
    model_name = "tag"
    DARK_COLOR = "#101010"
    LIGHT_COLOR = "#EFEFEF"

    color = models.CharField(
        verbose_name=_("Color"),
        max_length=32,
        default=random_color,
        validators=[RegexValidator(r"^#[0-9a-fA-F]{6}$")],
    )
    last_used = models.DateTimeField(
        verbose_name=_("Last used"),
        default=timezone.now,
        blank=False,
    )

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = [Lower("name")]
        verbose_name = _("Tag")
        verbose_name_plural = _("Tags")

    @property
    def complementary_color(self):
        if not self.color:
            return self.DARK_COLOR

        r, g, b = [int(x, 16) for x in re.match("#(..)(..)(..)", self.color).groups()]
        yiq = ((r * 299) + (g * 587) + (b * 114)) // 1000
        if yiq >= 128:
            return self.DARK_COLOR
        else:
            return self.LIGHT_COLOR


class Tagged(GenericTaggedItemBase):
    tag = models.ForeignKey(
        Tag,
        verbose_name=_("Tag"),
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_items",
    )

    def save_base(self, *args, **kwargs):
        """
        Update last_used of the used tag, whenever it is used in a
        save-operation.
        """
        self.tag.last_used = timezone.now()
        self.tag.save()
        return super().save_base(*args, **kwargs)


class TaggableManager(TaggitTaggableManager):
    pass


class BMI(models.Model):
    model_name = "bmi"
    child = models.ForeignKey(
        "Child", on_delete=models.CASCADE, related_name="bmi", verbose_name=_("Child")
    )
    bmi = models.FloatField(blank=False, null=False, verbose_name=_("BMI"))
    date = models.DateField(
        blank=False, default=timezone.localdate, null=False, verbose_name=_("Date")
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-date"]
        verbose_name = _("BMI")
        verbose_name_plural = _("BMI")

    def __str__(self):
        return str(_("BMI"))

    def clean(self):
        validate_date(self.date, "date")


class Child(models.Model):
    model_name = "child"
    first_name = models.CharField(max_length=255, verbose_name=_("First name"))
    last_name = models.CharField(
        blank=True, max_length=255, verbose_name=_("Last name")
    )
    birth_date = models.DateField(blank=False, null=False, verbose_name=_("Birth date"))
    birth_time = models.TimeField(blank=True, null=True, verbose_name=_("Birth time"))
    slug = models.SlugField(
        allow_unicode=True,
        blank=False,
        editable=False,
        max_length=100,
        unique=True,
        verbose_name=_("Slug"),
    )
    picture = models.ImageField(
        blank=True, null=True, upload_to="child/picture/", verbose_name=_("Picture")
    )

    objects = models.Manager()

    cache_key_count = "core.child.count"

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["last_name", "first_name"]
        verbose_name = _("Child")
        verbose_name_plural = _("Children")

    def __str__(self):
        return self.name()

    def save(self, *args, **kwargs):
        self.slug = slugify(self, allow_unicode=True)
        super(Child, self).save(*args, **kwargs)
        cache.set(self.cache_key_count, Child.objects.count(), None)

    def delete(self, using=None, keep_parents=False):
        super(Child, self).delete(using, keep_parents)
        cache.set(self.cache_key_count, Child.objects.count(), None)

    def name(self, reverse=False):
        if not self.last_name:
            return self.first_name
        if reverse:
            return "{}, {}".format(self.last_name, self.first_name)
        return "{} {}".format(self.first_name, self.last_name)

    def birth_datetime(self):
        if self.birth_time:
            return timezone.make_aware(
                datetime.datetime.combine(self.birth_date, self.birth_time)
            )
        return self.birth_date

    @classmethod
    def count(cls):
        """Get a (cached) count of total number of Child instances."""
        return cache.get_or_set(cls.cache_key_count, Child.objects.count, None)


class CoreModelBase(models.Model):
    mqtt_client = None

    class Meta:
        abstract = True

    def _as_json_payload(self):
        payload = {}
        for field in self._meta.fields:
            value = getattr(self, field.name)
            if isinstance(value, datetime.datetime):
                serialized = value.isoformat()
            elif isinstance(value, Child):
                serialized = value.id
            else:
                serialized = value
            payload[field.name] = serialized

        return json.dumps(
            {
                "event": "save",
                "model": self.model_name if hasattr(self, "model_name") else None,
                "payload": payload,
            }
        )

    def _init_mqtt_client(self, mqtt_config):
        if self.mqtt_client is None:

            def connect_mqtt():
                def on_connect(client, userdata, flags, rc):
                    if rc != 0:
                        raise RuntimeError(f"MQTT connection failed with code {rc}")

                from paho.mqtt import client as mqtt_client

                client = mqtt_client.Client(
                    client_id=mqtt_config["client_id"],
                    callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
                )

                username, password = mqtt_config["username"], mqtt_config["password"]
                client.username_pw_set(username, password)
                client.on_connect = on_connect
                client.connect(mqtt_config["host"], mqtt_config["port"])
                return client

            self.mqtt_client = connect_mqtt()

        return self.mqtt_client

    def _publish_to_mqtt(self):
        if settings.MQTT["host"]:
            payload = self._as_json_payload()
            client = self._init_mqtt_client(settings.MQTT)
            client.publish(settings.MQTT["topic"], payload)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # save first to get IDs and whatnot populated
        self._publish_to_mqtt()  # does nothing if MQTT config isn't defined or is None


class DiaperChange(CoreModelBase):
    model_name = "diaperchange"
    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="diaper_change",
        verbose_name=_("Child"),
    )
    time = models.DateTimeField(
        blank=False, default=timezone.localtime, null=False, verbose_name=_("Time")
    )
    wet = models.BooleanField(verbose_name=_("Wet"))
    solid = models.BooleanField(verbose_name=_("Solid"))
    color = models.CharField(
        blank=True,
        choices=[
            ("black", _("Black")),
            ("brown", _("Brown")),
            ("green", _("Green")),
            ("yellow", _("Yellow")),
        ],
        max_length=255,
        verbose_name=_("Color"),
    )
    amount = models.FloatField(blank=True, null=True, verbose_name=_("Amount"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-time"]
        verbose_name = _("Diaper Change")
        verbose_name_plural = _("Diaper Changes")

    def __str__(self):
        return str(_("Diaper Change"))

    def attributes(self):
        attributes = []
        if self.wet:
            attributes.append(self._meta.get_field("wet").verbose_name)
        if self.solid:
            attributes.append(self._meta.get_field("solid").verbose_name)
        if self.color:
            attributes.append(self.get_color_display())
        return attributes

    def clean(self):
        validate_time(self.time, "time")


class Feeding(models.Model):
    model_name = "feeding"
    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="feeding",
        verbose_name=_("Child"),
    )
    start = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Start time"),
    )
    end = models.DateTimeField(
        blank=False, default=timezone.localtime, null=False, verbose_name=_("End time")
    )
    duration = models.DurationField(
        editable=False, null=True, verbose_name=_("Duration")
    )
    type = models.CharField(
        choices=[
            ("breast milk", _("Breast milk")),
            ("formula", _("Formula")),
            ("fortified breast milk", _("Fortified breast milk")),
            ("solid food", _("Solid food")),
        ],
        max_length=255,
        verbose_name=_("Type"),
    )
    method = models.CharField(
        choices=[
            ("bottle", _("Bottle")),
            ("left breast", _("Left breast")),
            ("right breast", _("Right breast")),
            ("both breasts", _("Both breasts")),
            ("parent fed", _("Parent fed")),
            ("self fed", _("Self fed")),
        ],
        max_length=255,
        verbose_name=_("Method"),
    )
    amount = models.FloatField(blank=True, null=True, verbose_name=_("Amount"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-start"]
        verbose_name = _("Feeding")
        verbose_name_plural = _("Feedings")

    def __str__(self):
        return str(_("Feeding"))

    def save(self, *args, **kwargs):
        if self.start and self.end:
            self.duration = timezone_aware_duration(self.start, self.end)
        super(Feeding, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, "start")
        validate_duration(self)
        validate_unique_period(Feeding.objects.filter(child=self.child), self)


class HeadCircumference(models.Model):
    model_name = "head_circumference"
    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="head_circumference",
        verbose_name=_("Child"),
    )
    head_circumference = models.FloatField(
        blank=False, null=False, verbose_name=_("Head Circumference")
    )
    date = models.DateField(
        blank=False, default=timezone.localdate, null=False, verbose_name=_("Date")
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-date"]
        verbose_name = _("Head Circumference")
        verbose_name_plural = _("Head Circumference")

    def __str__(self):
        return str(_("Head Circumference"))

    def clean(self):
        validate_date(self.date, "date")


class Height(models.Model):
    model_name = "height"
    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="height",
        verbose_name=_("Child"),
    )
    height = models.FloatField(blank=False, null=False, verbose_name=_("Height"))
    date = models.DateField(
        blank=False, default=timezone.localdate, null=False, verbose_name=_("Date")
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-date"]
        verbose_name = _("Height")
        verbose_name_plural = _("Height")

    def __str__(self):
        return str(_("Height"))

    def clean(self):
        validate_date(self.date, "date")


class HeightPercentile(models.Model):
    model_name = "height percentile"
    age_in_days = models.DurationField(null=False)
    p3_height = models.FloatField(null=False)
    p15_height = models.FloatField(null=False)
    p50_height = models.FloatField(null=False)
    p85_height = models.FloatField(null=False)
    p97_height = models.FloatField(null=False)
    sex = models.CharField(
        null=False,
        max_length=255,
        choices=[
            ("girl", _("Girl")),
            ("boy", _("Boy")),
        ],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["age_in_days", "sex"], name="unique_age_sex_height"
            )
        ]


class Note(models.Model):
    model_name = "note"
    child = models.ForeignKey(
        "Child", on_delete=models.CASCADE, related_name="note", verbose_name=_("Child")
    )
    note = models.TextField(verbose_name=_("Note"))
    time = models.DateTimeField(
        blank=False, default=timezone.localtime, verbose_name=_("Time")
    )
    image = models.ImageField(
        blank=True, null=True, upload_to="notes/images/", verbose_name=_("Image")
    )
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-time"]
        verbose_name = _("Note")
        verbose_name_plural = _("Notes")

    def __str__(self):
        return str(_("Note"))


class Pumping(models.Model):
    model_name = "pumping"
    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="pumping",
        verbose_name=_("Child"),
    )
    start = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Start time"),
    )
    end = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("End time"),
    )
    duration = models.DurationField(
        editable=False,
        null=True,
        verbose_name=_("Duration"),
    )
    amount = models.FloatField(blank=False, null=False, verbose_name=_("Amount"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-start"]
        verbose_name = _("Pumping")
        verbose_name_plural = _("Pumping")

    def __str__(self):
        return str(_("Pumping"))

    def save(self, *args, **kwargs):
        if self.start and self.end:
            self.duration = timezone_aware_duration(self.start, self.end)
        super(Pumping, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, "start")
        validate_duration(self)
        validate_unique_period(Pumping.objects.filter(child=self.child), self)


class Sleep(models.Model):
    model_name = "sleep"
    child = models.ForeignKey(
        "Child", on_delete=models.CASCADE, related_name="sleep", verbose_name=_("Child")
    )
    start = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Start time"),
    )
    end = models.DateTimeField(
        blank=False, default=timezone.localtime, null=False, verbose_name=_("End time")
    )
    nap = models.BooleanField(null=False, blank=True, verbose_name=_("Nap"))
    duration = models.DurationField(
        editable=False, null=True, verbose_name=_("Duration")
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()
    settings = NapSettings(_("Nap settings"))

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-start"]
        verbose_name = _("Sleep")
        verbose_name_plural = _("Sleep")

    def __str__(self):
        return str(_("Sleep"))

    def save(self, *args, **kwargs):
        if self.nap is None:
            self.nap = (
                Sleep.settings.nap_start_min
                <= timezone.localtime(self.start).time()
                <= Sleep.settings.nap_start_max
            )
        if self.start and self.end:
            self.duration = timezone_aware_duration(self.start, self.end)
        super(Sleep, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, "start")
        validate_time(self.end, "end")
        validate_duration(self)
        validate_unique_period(Sleep.objects.filter(child=self.child), self)


class Temperature(models.Model):
    model_name = "temperature"
    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="temperature",
        verbose_name=_("Child"),
    )
    temperature = models.FloatField(
        blank=False, null=False, verbose_name=_("Temperature")
    )
    time = models.DateTimeField(
        blank=False, default=timezone.localtime, null=False, verbose_name=_("Time")
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-time"]
        verbose_name = _("Temperature")
        verbose_name_plural = _("Temperature")

    def __str__(self):
        return str(_("Temperature"))

    def clean(self):
        validate_time(self.time, "time")


class Timer(models.Model):
    model_name = "timer"
    child = models.ForeignKey(
        "Child",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="timers",
        verbose_name=_("Child"),
    )
    name = models.CharField(
        blank=True, max_length=255, null=True, verbose_name=_("Name")
    )
    start = models.DateTimeField(
        default=timezone.now, blank=False, verbose_name=_("Start time")
    )
    active = models.BooleanField(default=True, editable=False, verbose_name=_("Active"))
    user = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="timers",
        verbose_name=_("User"),
    )

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-start"]
        verbose_name = _("Timer")
        verbose_name_plural = _("Timers")

    def __str__(self):
        return self.name or str(format_lazy(_("Timer #{id}"), id=self.id))

    @property
    def title_with_child(self):
        """Get Timer title with child name in parenthesis."""
        title = str(self)
        # Only actually add the name if there is more than one Child instance.
        if title and self.child and Child.count() > 1:
            title = format_lazy("{title} ({child})", title=title, child=self.child)
        return title

    @property
    def user_username(self):
        """Get Timer user's name with a preference for the full name."""
        if self.user.get_full_name():
            return self.user.get_full_name()
        return self.user.get_username()

    def duration(self):
        return timezone.now() - self.start

    def restart(self):
        """Restart the timer."""
        self.start = timezone.now()
        self.save()

    def stop(self):
        """Stop (delete) the timer."""
        self.delete()

    def save(self, *args, **kwargs):
        self.name = self.name or None
        super(Timer, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, "start")


class TummyTime(models.Model):
    model_name = "tummytime"
    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="tummy_time",
        verbose_name=_("Child"),
    )
    start = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Start time"),
    )
    end = models.DateTimeField(
        blank=False, default=timezone.localtime, null=False, verbose_name=_("End time")
    )
    duration = models.DurationField(
        editable=False, null=True, verbose_name=_("Duration")
    )
    milestone = models.CharField(
        blank=True, max_length=255, verbose_name=_("Milestone")
    )
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-start"]
        verbose_name = _("Tummy Time")
        verbose_name_plural = _("Tummy Time")

    def __str__(self):
        return str(_("Tummy Time"))

    def save(self, *args, **kwargs):
        if self.start and self.end:
            self.duration = timezone_aware_duration(self.start, self.end)
        super(TummyTime, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, "start")
        validate_time(self.end, "end")
        validate_duration(self)
        validate_unique_period(TummyTime.objects.filter(child=self.child), self)


class Weight(models.Model):
    model_name = "weight"
    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="weight",
        verbose_name=_("Child"),
    )
    weight = models.FloatField(blank=False, null=False, verbose_name=_("Weight"))
    date = models.DateField(
        blank=False, default=timezone.localdate, null=False, verbose_name=_("Date")
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-date"]
        verbose_name = _("Weight")
        verbose_name_plural = _("Weight")

    def __str__(self):
        return str(_("Weight"))

    def clean(self):
        validate_date(self.date, "date")


class WeightPercentile(models.Model):
    model_name = "weight percentile"
    age_in_days = models.DurationField(null=False)
    p3_weight = models.FloatField(null=False)
    p15_weight = models.FloatField(null=False)
    p50_weight = models.FloatField(null=False)
    p85_weight = models.FloatField(null=False)
    p97_weight = models.FloatField(null=False)
    sex = models.CharField(
        null=False,
        max_length=255,
        choices=[
            ("girl", _("Girl")),
            ("boy", _("Boy")),
        ],
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["age_in_days", "sex"], name="unique_age_sex"
            )
        ]

    def __str__(self):
        return f"Sex: {self.sex}, Age: {self.age_in_days} days, p3: {self.p3_weight} kg, p15: {self.p15_weight} kg, p50: {self.p50_weight} kg, p85: {self.p85_weight} kg, p97: {self.p97_weight} kg"
