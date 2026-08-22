# -*- coding: utf-8 -*-
import datetime
import re

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F
from django.db.models.functions import Greatest, Lower, Now
from django.urls import reverse
from django.utils import formats, timezone
from django.utils.safestring import mark_safe
from django.utils.text import format_lazy, slugify
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager as TaggitTaggableManager
from taggit.models import GenericTaggedItemBase, TagBase

from babybuddy.site_settings import NapSettings, FeedingSettings, LowStockSettings, FormulaClockSettings, PumpingMethodSettings
from core.utils import random_color, timezone_aware_duration, to_household


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


def _format_dt(dt):
    return formats.date_format(timezone.localtime(dt), "SHORT_DATETIME_FORMAT")


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
        conflicting = queryset.filter(start__lt=model.end, end__gt=model.start).first()
        if conflicting:
            url = reverse(
                f"core:{conflicting.model_name}-update",
                args=[conflicting.id],
            )
            link = (
                f'<a href="{url}">{conflicting} '
                f"({_format_dt(conflicting.start)} - "
                f"{_format_dt(conflicting.end)})</a>"
            )
            raise ValidationError(
                mark_safe(
                    f'{_("Another entry intersects the specified time period.")} '
                    f'{_("Conflicting entry")}: {link}'
                ),
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


class SyncTimestampMixin(models.Model):
    """
    Mixin for models that participate in bb-sync. Tracks when a record was
    last edited by a user (not by sync operations) so push/merge can detect
    conflicts.

    - sync_updated_at is set on user-initiated saves only (forms, API, admin).
    - Sync operations set _sync_silent = True on the instance before saving
      (or use queryset.update() which bypasses save() entirely).
    - null=True, default=None: existing records start as "never edited" —
      treated as older than any watermark by both push and merge.
    """

    sync_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
        editable=False,
        verbose_name=_("Last user edit (sync tracking)"),
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not getattr(self, "_sync_silent", False):
            self.sync_updated_at = timezone.now()
        super().save(*args, **kwargs)


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


class BMI(SyncTimestampMixin, models.Model):
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
        ordering = ["-date", "-id"]
        verbose_name = _("BMI")
        verbose_name_plural = _("BMI")

    def __str__(self):
        return str(_("BMI"))

    def clean(self):
        validate_date(self.date, "date")


class Child(SyncTimestampMixin, models.Model):
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
    inventory_tracking_start = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Inventory tracking start"),
        help_text=_(
            "Earliest date/time diaper changes can decrement inventory "
            "for this child. Set to when you first started tracking "
            "diaper inventory. Changes before this date have no "
            "inventory impact."
        ),
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


class DiaperChange(SyncTimestampMixin, models.Model):
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
            ("gray", _("Gray")),
            ("green", _("Green")),
            ("orange", _("Orange")),
            ("red", _("Red")),
            ("white", _("White")),
            ("yellow", _("Yellow")),
        ],
        max_length=255,
        verbose_name=_("Color"),
    )
    amount = models.FloatField(blank=True, null=True, verbose_name=_("Amount"))
    wet_amount = models.CharField(
        blank=True,
        choices=[
            ("", _("---------")),
            ("trace", _("Trace")),
            ("light", _("Light")),
            ("moderate", _("Moderate")),
            ("heavy", _("Heavy")),
        ],
        default="",
        max_length=255,
        verbose_name=_("Wet amount"),
    )
    solid_amount = models.CharField(
        blank=True,
        choices=[
            ("", _("---------")),
            ("trace", _("Trace")),
            ("light", _("Light")),
            ("moderate", _("Moderate")),
            ("heavy", _("Heavy")),
        ],
        default="",
        max_length=255,
        verbose_name=_("Solid amount"),
    )
    blowout = models.CharField(
        blank=True,
        default="",
        max_length=10,
        choices=[
            ("", _("---------")),
            ("none", _("No blowout")),
            ("minor", _("Minor")),
            ("moderate", _("Moderate")),
            ("major", _("Major")),
        ],
        verbose_name=_("Blowout"),
    )
    blowout_direction = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Blowout direction"),
    )
    diaper_size = models.CharField(
        blank=True,
        choices=[
            ("", _("---------")),
            ("P", _("P (Preemie)")),
            ("NB", _("NB (Newborn)")),
            ("1", _("1")),
            ("2", _("2")),
            ("3", _("3")),
            ("4", _("4")),
            ("5", _("5")),
            ("6", _("6")),
        ],
        default="",
        max_length=255,
        verbose_name=_("Diaper size"),
    )
    diaper_brand = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Diaper brand"),
    )
    diaper_line = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Diaper line"),
    )
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
        # Build wet/solid with inline amounts
        if self.wet:
            parts = [str(self._meta.get_field("wet").verbose_name)]
            if self.wet_amount:
                parts.append(self.get_wet_amount_display())
            attributes.append(" ".join(parts))
        if self.solid:
            parts = [str(self._meta.get_field("solid").verbose_name)]
            if self.solid_amount:
                parts.append(self.get_solid_amount_display())
            if self.color:
                parts.append(self.get_color_display())
            attributes.append(" ".join(parts))
        elif self.color:
            # Color without solid (e.g., standalone color tracking)
            attributes.append(self.get_color_display())
        if self.blowout and self.blowout != "none":
            blowout_parts = [self.get_blowout_display()]
            if self.blowout_direction:
                blowout_parts.append(self.blowout_direction)
            attributes.append(" ".join(str(p) for p in blowout_parts))
        return attributes

    def clean(self):
        validate_time(self.time, "time")


class Feeding(SyncTimestampMixin, models.Model):
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
            ("tube", _("Tube feeding")),
            ("cup feeding", _("Cup feeding")),
            ("finger feeding", _("Finger feeding")),
            ("syringe", _("Syringe")),
        ],
        max_length=255,
        verbose_name=_("Method"),
    )
    amount = models.FloatField(blank=True, null=True, verbose_name=_("Amount"))
    amount_unit = models.CharField(
        blank=True,
        default="ml",
        max_length=5,
        choices=[
            ("ml", _("ml")),
            ("oz", _("oz")),
            ("tsp", _("tsp")),
            ("tbsp", _("tbsp")),
        ],
        verbose_name=_("Amount unit"),
    )
    amount_normalized = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Amount (normalized)"),
    )
    breastfeeding_modifier = models.CharField(
        blank=True,
        null=True,
        choices=[
            ("none", _("None")),
            ("nipple_shield", _("Nipple shield")),
            ("nipple_shield_sns", _("Nipple shield + SNS")),
        ],
        default="none",
        max_length=255,
        verbose_name=_("Breastfeeding modifier"),
    )
    sns_amount = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("SNS amount"),
    )
    sns_milk_type = models.CharField(
        blank=True,
        null=True,
        choices=[
            ("breast milk", _("Breast milk")),
            ("formula", _("Formula")),
        ],
        default="",
        max_length=255,
        verbose_name=_("SNS milk type"),
    )
    nipple_size = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Nipple size"),
    )
    formula_brand = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Formula brand"),
    )
    bottle_brand = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Bottle brand"),
    )
    bottle_model = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Bottle model"),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)
    previous_feeding = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="continuations",
        verbose_name=_("Previous feeding"),
        help_text=_("Link to a feeding this continues (back-to-back sessions)."),
    )
    feed_inventory = models.ForeignKey(
        "FeedInventory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedings",
        verbose_name=_("Feed inventory item"),
        help_text=_(
            "Optional. Link to a Milk Inventory item to decrement its "
            "remaining amount by this feeding's amount."
        ),
    )
    prepared_feed = models.ForeignKey(
        "PreparedFeed",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedings",
        verbose_name=_("Prepared bottle"),
        help_text=_(
            "Optional. Link to a prepared formula bottle to decrement "
            "its remaining amount (ml) by this feeding's amount."
        ),
    )
    formula_stock = models.ForeignKey(
        "FormulaStock",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedings",
        verbose_name=_("Formula source"),
        help_text=_(
            "Optional. Link to an opened formula container (powder or "
            "ready-to-feed) to decrement it by this feeding."
        ),
    )
    # T6 inline prep — nullable ml capture for powder picks. When
    # amount_mixed > amount fed, a PreparedFeed unit is created at save
    # time and linked via prepared_feed (formula_stock stays null). NULL
    # or == fed keeps direct-pool behavior. Persisted for edit
    # re-derivation (restore/re-deduct of pool grams on edits).
    amount_mixed = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Amount mixed (ml)"),
        help_text=_(
            "Powder inline prep: total ml mixed. Exceeding the amount fed "
            "creates a prepared bottle for the leftover."
        ),
    )

    settings = FeedingSettings()

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-start"]
        verbose_name = _("Feeding")
        verbose_name_plural = _("Feedings")

    def __str__(self):
        return str(_("Feeding"))

    def save(self, *args, **kwargs):
        # Capture previous state so linked inventory consumption can be
        # adjusted (create, edit, unlink) instead of double-decrementing.
        # Covers milk (feed_inventory), formula stock (formula_stock) and
        # prepared bottles (prepared_feed).
        previous = None
        if self.pk is not None:
            previous = (
                Feeding.objects.filter(pk=self.pk)
                .only(
                    "feed_inventory",
                    "prepared_feed",
                    "formula_stock",
                    "amount_normalized",
                )
                .first()
            )
        if self.start and self.end:
            self.duration = timezone_aware_duration(self.start, self.end)
        # Normalize amount to ml for cross-unit aggregation
        if self.amount is not None:
            if self.amount_unit == "oz":
                self.amount_normalized = round(self.amount * 29.5735, 1)
            elif self.amount_unit == "tsp":
                self.amount_normalized = round(self.amount * 5, 1)
            elif self.amount_unit == "tbsp":
                self.amount_normalized = round(self.amount * 15, 1)
            else:
                self.amount_normalized = self.amount
        else:
            self.amount_normalized = None

        # T6 inline prep — powder pick with amount mixed > amount fed
        # creates a PreparedFeed unit for the leftover BEFORE the FKs
        # persist: the unit's own save() decrements the pool for the
        # FULL mixed grams (prep-flow precedent), and the existing
        # prepared-bottle machinery below carries this feeding's
        # consumption (fed ml off the unit, first_fed_at, ledger,
        # status lifecycle). formula_stock swaps to null so the
        # at-most-one-source rule holds by construction.
        if (
            self.formula_stock_id
            and self.prepared_feed_id is None
            and self.amount_mixed is not None
            and self.amount_normalized is not None
            and self.amount_mixed > self.amount_normalized
        ):
            stock = FormulaStock.objects.filter(
                pk=self.formula_stock_id
            ).first()
            if stock and stock.form == "powder":
                unit = PreparedFeed(
                    source_pool=stock,
                    prepared_from="powder_mix",
                    amount=self.amount_mixed,
                    amount_remaining=self.amount_mixed,
                    prepared_at=self.start or timezone.now(),
                    status="active",
                    notes="Inline prep at feed time",
                )
                unit.save()
                self.prepared_feed = unit
                self.formula_stock = None

        # T6 inline-prep edit sync — unit-linked feeding whose amount
        # mixed changed: re-derive the unit. amount/amount_remaining
        # shift by the delta (clamped ≥ 0); the unit's own save()
        # restores the old pool grams and decrements the new (ledger
        # both directions). Fed-ml edits ride the normal prepared
        # branch below.
        elif (
            self.prepared_feed_id
            and self.amount_mixed is not None
        ):
            unit = PreparedFeed.objects.filter(
                pk=self.prepared_feed_id
            ).first()
            if unit and self.amount_mixed != unit.amount:
                delta = self.amount_mixed - unit.amount
                remaining = unit.amount_remaining
                if remaining is None:
                    remaining = unit.amount
                unit.amount = self.amount_mixed
                unit.amount_remaining = max(0.0, remaining + delta)
                unit.save()
                if unit.status == "active" and unit.amount_remaining <= 0:
                    PreparedFeed.objects.filter(pk=unit.pk).update(
                        status="consumed"
                    )

        super(Feeding, self).save(*args, **kwargs)
        self._adjust_feed_inventory(previous)
        self._adjust_formula_inventory(previous)

    def _adjust_feed_inventory(self, previous):
        """Decrement the linked FeedInventory by this feeding's amount (ml).

        Restores any previous consumption first so edits (amount or item
        change) and unlinks net out correctly. Remaining amount is clamped
        at 0 so a feeding can never drive inventory negative.
        """
        old_item = previous.feed_inventory if previous else None
        old_amount = previous.amount_normalized if previous else None
        new_item = self.feed_inventory
        new_amount = self.amount_normalized
        old_item_id = old_item.pk if old_item else None
        new_item_id = new_item.pk if new_item else None

        if old_item_id == new_item_id and old_amount == new_amount:
            return

        # Restore: return the old consumption to the old item
        if old_item_id is not None and old_amount:
            FeedInventory.objects.filter(pk=old_item_id).update(
                amount_remaining=F("amount_remaining") + old_amount
            )
            _item = FeedInventory.objects.get(pk=old_item_id)
            _item.record_event(
                "feeding_restored", amount_delta=+old_amount, feeding=self,
                note="Feeding edit/unlink restored consumption",
            )

        # Decrement: subtract the new consumption from the new item
        if new_item_id is not None and new_amount:
            FeedInventory.objects.filter(pk=new_item_id).update(
                amount_remaining=Greatest(0.0, F("amount_remaining") - new_amount)
            )
            _item = FeedInventory.objects.get(pk=new_item_id)
            _item.record_event(
                "feeding_consumed", amount_delta=-new_amount, feeding=self,
                note="Feeding consumed from inventory",
            )

    @staticmethod
    def _powder_grams(line, amount_ml):
        """grams = amount_ml × scoop_grams / water_per_scoop_ml.

        Basis: label ratios are per WATER volume, logged amount is the
        FINAL bottle volume (water ≈ 90%). Water-basis math slightly
        under-decrements (~9% drift) — accepted; physical counts correct
        drift. Documented in docs/formula-inventory.md.
        """
        if not line.scoop_grams or not line.water_per_scoop_ml or not amount_ml:
            return None
        return round(
            amount_ml * line.scoop_grams / line.water_per_scoop_ml, 2
        )

    def _stock_delta(self, stock, amount_ml):
        """(kind, qty) a feeding of amount_ml draws from stock.

        RTF: ml direct. Powder: grams via scoop ratio (None when the
        pool's ratio fields are unset — no decrement possible).
        """
        if stock.form == "rtf":
            return ("ml", amount_ml)
        return ("grams", self._powder_grams(stock.product_line, amount_ml))

    def _resolve_formula_stock(self):
        """Explicit selection wins; brand-only legacy fallback auto-picks
        an opened powder pool in drain order (powder only — RTF requires
        an explicit selection). Formula-type feedings only; fortified
        breast milk keeps the milk-inventory flow.
        """
        if self.formula_stock_id:
            return self.formula_stock
        if self.prepared_feed_id:
            return None
        if self.type != "formula" or not self.formula_brand:
            return None
        return (
            FormulaStock.objects.filter(
                product_line__item_type="formula",
                product_line__brand=self.formula_brand,
                form="powder",
                opened_at__isnull=False,
            )
            # Reserves are never decrementable — not even as the last
            # resort of the auto-pick fallback (matches the diaper-side
            # convention in core/signals.py). Using a reserve means
            # unchecking Reserve on the pool first.
            .exclude(is_reserve=True)
            .order_by("-drain_priority", "opened_at")
            .first()
        )

    def _restore_stock_consumption(self, stock, old_amount):
        """Return old consumption to a formula stock pool (+ledger)."""
        kind, qty = self._stock_delta(stock, old_amount)
        if not qty:
            return
        if kind == "ml":
            FormulaStock.objects.filter(pk=stock.pk).update(
                ml_remaining=F("ml_remaining") + qty
            )
            ev = {"delta_ml": +qty}
        else:
            FormulaStock.objects.filter(pk=stock.pk).update(
                grams_remaining=F("grams_remaining") + qty
            )
            ev = {"delta_grams": +qty}
        stock.refresh_from_db()
        stock.record_event(
            "feeding_restored",
            grams_after=stock.grams_remaining,
            ml_after=stock.ml_remaining,
            source_id=self.pk,
            note="Feeding edit/unlink restored consumption",
            **ev,
        )

    def _decrement_stock(self, stock):
        """Apply this feeding's consumption to a formula stock pool
        (clamped at 0, +ledger)."""
        kind, qty = self._stock_delta(stock, self.amount_normalized)
        if not qty:
            return
        if kind == "ml":
            FormulaStock.objects.filter(pk=stock.pk).update(
                ml_remaining=Greatest(0.0, F("ml_remaining") - qty)
            )
            ev = {"delta_ml": -qty}
        else:
            FormulaStock.objects.filter(pk=stock.pk).update(
                grams_remaining=Greatest(0.0, F("grams_remaining") - qty)
            )
            ev = {"delta_grams": -qty}
        stock.refresh_from_db()
        stock.record_event(
            "feeding_decrement",
            grams_after=stock.grams_remaining,
            ml_after=stock.ml_remaining,
            source_id=self.pk,
            note="Feeding consumed from formula stock",
            **ev,
        )

    def _adjust_formula_inventory(self, previous):
        """Formula-side counterpart of _adjust_feed_inventory.

        Restore-then-decrement contract, clamp ≥ 0, ledger both
        directions, covering prepared bottles (ml direct) and formula
        stock pools (RTF ml direct, powder grams via ratio). The brand-
        only fallback resolution is persisted onto the feeding so a
        later edit restores the exact pool.
        """
        new_stock = self._resolve_formula_stock()
        if (
            new_stock is not None
            and self.formula_stock_id != new_stock.pk
        ):
            self.formula_stock = new_stock
            if self.pk:
                Feeding.objects.filter(pk=self.pk).update(
                    formula_stock=new_stock
                )

        old_amount = previous.amount_normalized if previous else None

        # --- PreparedFeed: restore-then-decrement (ml, direct) ---
        old_prepared_id = (
            previous.prepared_feed_id if previous else None
        )
        new_prepared_id = self.prepared_feed_id
        if not (
            old_prepared_id == new_prepared_id
            and old_amount == self.amount_normalized
        ):
            if old_prepared_id is not None and old_amount:
                PreparedFeed.objects.filter(pk=old_prepared_id).update(
                    amount_remaining=F("amount_remaining") + old_amount
                )
                pf = PreparedFeed.objects.get(pk=old_prepared_id)
                pf.record_event(
                    "feeding_restored",
                    delta_ml=+old_amount,
                    ml_after=pf.amount_remaining,
                    source_id=self.pk,
                    note="Feeding edit/unlink restored consumption",
                )
                # T4 status lifecycle: undo the auto-consumed flip when the
                # restore leaves usable milk in the unit. amount_remaining
                # is the single source of truth (other live consumptions
                # are already reflected in it); manual discarded state is
                # never touched.
                if pf.status == "consumed" and pf.amount_remaining > 0:
                    PreparedFeed.objects.filter(pk=old_prepared_id).update(
                        status="active"
                    )
            if new_prepared_id is not None and self.amount_normalized:
                PreparedFeed.objects.filter(pk=new_prepared_id).update(
                    amount_remaining=Greatest(
                        0.0, F("amount_remaining") - self.amount_normalized
                    )
                )
                pf = PreparedFeed.objects.get(pk=new_prepared_id)
                if pf.first_fed_at is None:
                    PreparedFeed.objects.filter(pk=new_prepared_id).update(
                        first_fed_at=self.start or timezone.now()
                    )
                pf.record_event(
                    "feeding_decrement",
                    delta_ml=-self.amount_normalized,
                    ml_after=pf.amount_remaining,
                    source_id=self.pk,
                    note="Feeding consumed from prepared bottle",
                )
                # T4 status lifecycle: a drained bottle is consumed.
                # (Manual discard wins — only flip active → consumed.)
                if pf.status == "active" and pf.amount_remaining <= 0:
                    PreparedFeed.objects.filter(pk=new_prepared_id).update(
                        status="consumed"
                    )

        # --- FormulaStock: restore-then-decrement ---
        old_stock_id = previous.formula_stock_id if previous else None
        new_stock_id = new_stock.pk if new_stock else None
        if not (
            old_stock_id == new_stock_id
            and old_amount == self.amount_normalized
        ):
            if old_stock_id is not None and old_amount:
                stock = FormulaStock.objects.get(pk=old_stock_id)
                self._restore_stock_consumption(stock, old_amount)
            if new_stock_id is not None and self.amount_normalized:
                self._decrement_stock(new_stock)

    def clean(self):
        validate_time(self.start, "start")
        validate_duration(self)
        validate_unique_period(Feeding.objects.filter(child=self.child), self)
        # At most one inventory source per feeding (milk item, prepared
        # bottle, or formula container) — mixing them double-decrements.
        sources = [
            self.feed_inventory_id,
            self.prepared_feed_id,
            self.formula_stock_id,
        ]
        if sum(1 for s in sources if s) > 1:
            raise ValidationError(
                _(
                    "Select at most one inventory source: a milk "
                    "inventory item, a prepared bottle, or a formula "
                    "container."
                )
            )


class FeedingOption(models.Model):
    """
    Managed dropdown options for feeding form fields (bottle brand,
    bottle model, nipple size, formula brand).
    Parent FK enables cascading (nipple sizes scoped to bottle model).
    """

    FIELD_TYPES = [
        ("bottle_brand", _("Bottle brand")),
        ("bottle_model", _("Bottle model")),
        ("nipple_size", _("Nipple size")),
        ("formula_brand", _("Formula brand")),
    ]

    field_type = models.CharField(
        choices=FIELD_TYPES,
        max_length=50,
        verbose_name=_("Field type"),
    )
    value = models.CharField(
        max_length=255,
        verbose_name=_("Value"),
    )
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name=_("Parent option"),
    )

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["field_type", "value"]
        verbose_name = _("Feeding Option")
        verbose_name_plural = _("Feeding Options")
        constraints = [
            models.UniqueConstraint(
                fields=["field_type", "value", "parent"],
                name="unique_feeding_option",
            ),
        ]

    def __str__(self):
        return f"{self.get_field_type_display()}: {self.value}"


class HeadCircumference(SyncTimestampMixin, models.Model):
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
        ordering = ["-date", "-id"]
        verbose_name = _("Head Circumference")
        verbose_name_plural = _("Head Circumference")

    def __str__(self):
        return str(_("Head Circumference"))

    def clean(self):
        validate_date(self.date, "date")


class Height(SyncTimestampMixin, models.Model):
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
        ordering = ["-date", "-id"]
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


class Note(SyncTimestampMixin, models.Model):
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


class Pumping(SyncTimestampMixin, models.Model):
    model_name = "pumping"
    child = models.ForeignKey(
        "Child",
        on_delete=models.SET_NULL,
        related_name="pumping",
        verbose_name=_("Child"),
        blank=True,
        null=True,
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
    amount = models.FloatField(blank=True, null=True, verbose_name=_("Amount"))
    amount_unit = models.CharField(
        blank=True,
        default="ml",
        max_length=5,
        choices=[("ml", _("ml")), ("oz", _("oz"))],
        verbose_name=_("Amount unit"),
    )
    amount_normalized = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Amount (normalized)"),
    )
    method = models.CharField(
        blank=True,
        choices=[
            ("electric pump", _("Electric pump")),
            ("wearable pump", _("Wearable pump")),
            ("manual pump", _("Manual pump")),
            ("hand expression", _("Hand expression")),
        ],
        default="",
        max_length=255,
        verbose_name=_("Method"),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()
    settings = PumpingMethodSettings(_("Pumping settings"))

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-start"]
        verbose_name = _("Pumping")
        verbose_name_plural = _("Pumping")

    def __str__(self):
        # Descriptive label for dropdowns (FeedInventory pumping_session;
        # BD-9). Restores 270f72d0, lost in the Aug 5 dev rebuild.
        if self.start:
            from django.utils.formats import date_format

            label = date_format(self.start, "SHORT_DATETIME_FORMAT")
            if self.amount:
                label += f" ({self.amount})"
            return label
        return str(_("Pumping"))

    def save(self, *args, **kwargs):
        if self.start and self.end:
            self.duration = timezone_aware_duration(self.start, self.end)
        # Normalize amount to ml for cross-unit aggregation
        if self.amount is not None:
            if self.amount_unit == "oz":
                self.amount_normalized = round(self.amount * 29.5735, 1)
            else:
                self.amount_normalized = self.amount
        else:
            self.amount_normalized = None
        super(Pumping, self).save(*args, **kwargs)
        # FR-5: auto-create a FeedInventory entry when a new pumping record
        # is created. The inventory entry inherits the child, pumping_session
        # FK, and amount (normalized to ml) from this pumping record.
        # Amount-added-on-edit (2026-08-17): a log saved without an amount
        # that later gains one is treated as creation for inventory
        # purposes — the "not new, but the amount IS new" case. Guarded by
        # the existing-unit check so a double-fire can't duplicate.
        should_create_unit = self.amount_normalized and not FeedInventory.objects.filter(
            pumping_session=self
        ).exists()
        if should_create_unit:
            self._create_feed_inventory()

    def _create_feed_inventory(self):
        """Create a FeedInventory entry linked to this pumping session.

        B5 (2026-08-21): the sentinel 'Breast Milk' ProductLine
        (item_type='milk') is no longer created — FeedInventory rows
        stand alone (verified: no FK to ProductLine; nothing consumes
        the sentinel).
        """
        entry = FeedInventory.objects.create(
            child=self.child,
            pumping_session=self,
            type="breast_milk",
            amount=self.amount_normalized,
            amount_unit="ml",
            expressed_at=self.end or timezone.now(),
        )
        entry.record_event("created_from_pumping", pumping=self, amount_delta=0,
                           note="Auto-created from pumping session")

    def sync_unit_amount_if_pristine(self, at=None):
        """Sync-if-pristine (2026-08-17): on pumping edit, if this
        session's auto-created unit has never been touched (no ledger
        events beyond its creation, full amount remaining), adjust the
        unit to the log's current amount and record the adjustment.

        Returns (synced: bool, reason: str) so callers can surface a
        divergence notice when syncing was declined.
        """
        units = self.source_inventory.all()
        if not units.exists():
            return False, "no_unit"
        # A session can only have one directly created unit, but merges
        # keep the pumping_session FK on absorbed units too — only sync
        # when exactly one unit is linked (unambiguous survivor).
        if units.count() > 1:
            return False, "multi_unit"
        unit = units.first()
        events = FeedInventoryEvent.objects.filter(inventory=unit).exclude(
            type="created_from_pumping"
        )
        if events.exists():
            return False, "has_history"
        if unit.amount_remaining != unit.amount:
            return False, "touched_amount"
        at = at or timezone.now()
        delta = (self.amount_normalized or 0) - (unit.amount or 0)
        if abs(delta) < 0.05:
            return True, "no_change"
        old_amount = unit.amount
        unit.amount = self.amount_normalized
        unit.amount_remaining = self.amount_normalized
        unit.save()
        unit.record_event(
            "pumping_edit_adjusted",
            amount_delta=round(delta, 2),
            pumping=self,
            note="Pumping edit {} → {} ml (pristine unit synced)".format(
                old_amount, self.amount_normalized
            ),
        )
        return True, "synced"

    def clean(self):
        validate_time(self.start, "start")
        validate_duration(self)
        validate_unique_period(Pumping.objects.filter(child=self.child), self)


class Sleep(SyncTimestampMixin, models.Model):
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


class Temperature(SyncTimestampMixin, models.Model):
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


class TummyTime(SyncTimestampMixin, models.Model):
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


class Weight(SyncTimestampMixin, models.Model):
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
        ordering = ["-date", "-id"]
        verbose_name = _("Weight")
        verbose_name_plural = _("Weight")

    def __str__(self):
        return str(_("Weight"))

    def clean(self):
        validate_date(self.date, "date")


class Medication(SyncTimestampMixin, models.Model):
    model_name = "medication"

    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="medication",
        verbose_name=_("Child"),
        blank=False,
        null=False,
    )
    name = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        verbose_name=_("Medication Name"),
        help_text=_("Name of the medication administered"),
        db_index=True,
    )
    dosage = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Dosage"),
        help_text=_("Amount of medication given"),
    )
    dosage_unit = models.CharField(
        max_length=20,
        choices=[
            ("mg", _("MG")),
            ("ml", _("ML")),
            ("tablets", _("Tablets")),
            ("drops", _("Drops")),
        ],
        blank=True,
        null=False,
        default="",
        verbose_name=_("Dosage Unit"),
    )
    time = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Time Taken"),
        db_index=True,
    )
    next_dose_interval = models.DurationField(
        blank=True,
        null=True,
        verbose_name=_("Next Dose Interval"),
        help_text=_("Time until next dose can be given"),
    )
    doctor_visit = models.ForeignKey(
        "DoctorVisit",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="medications",
        verbose_name=_("Related Doctor Visit"),
        help_text=_("Link to the doctor visit that prescribed this medication."),
    )
    prescription = models.ForeignKey(
        "Prescription",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="doses",
        verbose_name=_("Prescription"),
        help_text=_("Standing prescription this dose is part of."),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        ordering = ["-time"]
        verbose_name = _("Medication")
        verbose_name_plural = _("Medications")
        default_permissions = ("view", "add", "change", "delete")

    @property
    def next_dose_time(self):
        """
        Calculate when the next dose can be given based on the time this dose
        was administered and the configured interval.
        :returns: a DateTime instance or None if no interval is set.
        """
        if self.next_dose_interval:
            return self.time + self.next_dose_interval
        return None

    @property
    def next_dose_ready(self):
        """
        Whether the next dose can be given (current time >= next_dose_time).
        :returns: True if next dose is ready, False otherwise, None if no interval set.
        """
        if self.next_dose_time:
            return timezone.now() >= self.next_dose_time
        return None

    def clean(self):
        validate_time(self.time, "time")

    def __str__(self):
        return str(_("Medication"))


class Prescription(models.Model):
    """
    A standing prescription for a child — the "what was prescribed" record,
    separate from Medication which is the "what was actually given" dose log.
    """

    model_name = "prescription"

    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="prescriptions",
        verbose_name=_("Child"),
        blank=False,
        null=False,
    )
    medication_name = models.CharField(
        max_length=255,
        blank=False,
        null=False,
        verbose_name=_("Medication Name"),
        help_text=_("Name of the prescribed medication"),
        db_index=True,
    )
    dosage = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Dosage"),
        help_text=_("Prescribed amount per dose"),
    )
    dosage_unit = models.CharField(
        max_length=20,
        choices=[
            ("mg", _("MG")),
            ("ml", _("ML")),
            ("tablets", _("Tablets")),
            ("drops", _("Drops")),
        ],
        blank=True,
        null=False,
        default="",
        verbose_name=_("Dosage Unit"),
    )
    frequency = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Frequency"),
        help_text=_("e.g., 'Every 6 hours', '3 times daily', 'As needed'"),
    )
    duration = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Duration"),
        help_text=_("e.g., '7 days', 'Ongoing', 'Until finished'"),
    )
    prescribing_doctor = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Prescribing Doctor"),
    )
    doctor_visit = models.ForeignKey(
        "DoctorVisit",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="prescriptions",
        verbose_name=_("Related Doctor Visit"),
        help_text=_("Visit where this was prescribed"),
    )
    active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Is this prescription currently active?"),
        db_index=True,
    )
    start_date = models.DateField(
        blank=False,
        default=Now,
        verbose_name=_("Start Date"),
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("End Date"),
        help_text=_("Leave blank if ongoing or unknown"),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        ordering = ["-start_date", "medication_name"]
        verbose_name = _("Prescription")
        verbose_name_plural = _("Prescriptions")
        default_permissions = ("view", "add", "change", "delete")

    def __str__(self):
        return (
            f"{self.medication_name}"
            if self.medication_name
            else str(_("Prescription"))
        )


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


class ProductLine(models.Model):
    """
    A brand+line combination — the product family that inventory items
    and feeding/diaper entries reference for consistent data.
    Examples: Pampers Swaddlers, Dr. Brown's Wide-Neck, Millie Moon (no line).
    """

    ITEM_TYPES = [
        ("diapers", _("Diapers")),
        ("wipes", _("Wipes")),
        ("formula", _("Formula")),
        ("bottle_nipples", _("Bottle nipples")),
        ("bottles", _("Bottles")),
        ("other", _("Other")),
    ]

    item_type = models.CharField(
        max_length=50, choices=ITEM_TYPES, verbose_name=_("Type")
    )
    brand = models.CharField(max_length=255, verbose_name=_("Brand"))
    line = models.CharField(
        blank=True, default="", max_length=255, verbose_name=_("Line")
    )

    # Formula ratio fields (formula-inventory DECISION #4): product-level
    # mixing facts. Nullable — RTF (ready-to-feed) lines carry none.
    scoop_grams = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Scoop grams"),
        help_text=_(
            "Powder only: grams per level scoop (e.g. 8.7). "
            "Ready-to-feed lines leave this blank."
        ),
    )
    water_per_scoop_ml = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Water per scoop (ml)"),
        help_text=_(
            "Powder only: ml of water per scoop (e.g. 60). "
            "Ready-to-feed lines leave this blank."
        ),
    )

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        constraints = [
            models.UniqueConstraint(
                fields=["item_type", "brand", "line"],
                name="unique_product_line",
            )
        ]
        ordering = ["item_type", "brand", "line"]
        verbose_name = _("Product Line")
        verbose_name_plural = _("Product Lines")

    def __str__(self):
        if self.line:
            return f"{self.brand} {self.line}"
        return self.brand


class SupplyItem(models.Model):
    """
    One inventory pool per product line + size. Household-scoped by
    default (child=None); child-scoped pools are supported and only
    match their own child's changes (signals/recalc/views include
    household pools for every child).
    quantity = live count of individual items remaining (decremented by change logs).
    Restocking adds to quantity; using diapers subtracts from it.
    """

    model_name = "supply_item"

    child = models.ForeignKey(
        "Child",
        on_delete=models.SET_NULL,
        related_name="supply_items",
        verbose_name=_("Child"),
        blank=True,
        null=True,
    )
    product_line = models.ForeignKey(
        ProductLine,
        on_delete=models.PROTECT,
        related_name="supply_items",
        verbose_name=_("Product"),
    )
    size = models.CharField(
        blank=True, default="", max_length=50, verbose_name=_("Size")
    )
    quantity = models.IntegerField(default=0, verbose_name=_("Quantity remaining"))
    initial_quantity = models.IntegerField(
        default=0, verbose_name=_("Initial quantity")
    )
    purchase_date = models.DateField(
        blank=True, null=True, verbose_name=_("Purchase date")
    )
    acquisition_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Acquisition date"),
        help_text=_(
            "When this stock was acquired (purchased, gifted, etc.). "
            "Diaper changes before this date won't decrement this pool."
        ),
    )
    usage_eligible = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Usage eligible from"),
        help_text=_(
            "Date/time from which this pool can be decremented by diaper "
            "changes. Defaults to the acquisition date when stock is put "
            "into rotation. Leave null (blank) for sealed or reserve "
            "stock that should not be touched."
        ),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    drain_priority = models.IntegerField(
        default=0,
        verbose_name=_("Drain priority"),
        help_text=_(
            "Higher = drained first. 0 = normal (FIFO by usage_eligible). "
            "Among same-priority pools, FIFO still applies."
        ),
    )
    is_reserve = models.BooleanField(
        default=False,
        verbose_name=_("Reserve stock"),
        help_text=_(
            "Check for items you do NOT intend to use (return candidates, "
            "gifts to regift, etc.). Excluded from burn rate calculations. "
            "Different from sealed — sealed items will eventually be opened."
        ),
    )
    is_retired = models.BooleanField(
        default=False,
        verbose_name=_("Retired"),
        help_text=_(
            "Retired pools are hidden from add/restock pickers and never "
            "decremented, but stay visible on the Supplies page for "
            "history. Use for sizes grown out of, etc."
        ),
    )

    objects = models.Manager()
    settings = LowStockSettings(_("Low stock settings"))

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = [
            "product_line__item_type",
            "product_line__brand",
            "product_line__line",
            "size",
        ]
        verbose_name = _("Supply Item")
        verbose_name_plural = _("Supply Items")

    def __str__(self):
        label = str(self.product_line)
        if self.size:
            label += f" [{self.size}]"
        label += f" (#{self.id})"
        return label


class SpitUp(models.Model):
    """
    Spit-up tracking — time, relative amount, appearance, optional link
    to preceding feeding. Enables correlation analysis (e.g., "does he
    spit up more after bottle feedings than breast?").
    """

    model_name = "spit_up"

    AMOUNT_CHOICES = [
        ("trace", _("Trace (just a spot)")),
        ("dribble", _("Dribble (a little)")),
        ("moderate", _("Moderate (noticeable)")),
        ("large", _("Large (soaks clothes)")),
        ("projectile", _("Projectile / lots")),
    ]

    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="spit_ups",
        verbose_name=_("Child"),
    )
    time = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Time"),
    )
    amount = models.CharField(
        max_length=50,
        choices=AMOUNT_CHOICES,
        blank=True,
        default="",
        verbose_name=_("Amount"),
    )
    appearance = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Appearance"),
        help_text=_("e.g., curdled, watery, clear, milky"),
    )
    related_feeding = models.ForeignKey(
        "Feeding",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="spit_ups",
        verbose_name=_("Related feeding"),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-time"]
        verbose_name = _("Spit-Up")
        verbose_name_plural = _("Spit-Up")

    def __str__(self):
        return str(_("Spit-Up"))


class EquipmentItem(models.Model):
    """
    Durable baby equipment — bottles, nipples, etc. NOT consumable.
    Each record represents one acquisition batch. Total owned is
    derived by summing quantity WHERE disposal_status='owned'.
    """

    model_name = "equipment"

    DISPOSAL_CHOICES = [
        ("owned", _("Owned")),
        ("given_away", _("Given away")),
        ("sold", _("Sold")),
        ("broken", _("Broken/Lost")),
    ]

    child = models.ForeignKey(
        "Child",
        on_delete=models.SET_NULL,
        related_name="equipment_items",
        verbose_name=_("Child"),
        blank=True,
        null=True,
    )
    product_line = models.ForeignKey(
        "ProductLine",
        on_delete=models.PROTECT,
        related_name="equipment_items",
        verbose_name=_("Product"),
    )
    size = models.CharField(
        blank=True,
        default="",
        max_length=50,
        verbose_name=_("Size"),
        help_text=_("e.g., NB flow, slow flow, 8oz, etc."),
    )
    quantity = models.IntegerField(
        default=1,
        verbose_name=_("Quantity"),
        help_text=_("How many in this acquisition."),
    )
    acquired_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Acquired date"),
    )
    source = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Source"),
        help_text=_("e.g., Amazon, baby shower, friend, hospital"),
    )
    disposal_status = models.CharField(
        max_length=50,
        choices=DISPOSAL_CHOICES,
        default="owned",
        verbose_name=_("Disposal status"),
    )
    disposal_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Disposal date"),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = [
            "product_line__item_type",
            "product_line__brand",
            "product_line__line",
            "size",
            "-acquired_date",
        ]
        verbose_name = _("Equipment Item")
        verbose_name_plural = _("Equipment Items")

    def __str__(self):
        return str(_("Equipment Item"))


class FeedInventory(SyncTimestampMixin, models.Model):
    """
    A stored unit of breast milk, donor milk, or prepared formula.
    Household-scoped — feed belongs to the household pool, not one
    specific child. The child FK is nullable because milk from any
    pumping session can feed any child.
    """
    model_name = "feed_inventory"

    child = models.ForeignKey(
        "Child",
        on_delete=models.SET_NULL,
        related_name="feed_inventory",
        verbose_name=_("Child"),
        blank=True,
        null=True,
        help_text=_("Optional. Leave blank for household milk pool."),
    )
    pumping_session = models.ForeignKey(
        "Pumping",
        on_delete=models.SET_NULL,
        related_name="source_inventory",
        verbose_name=_("Pumping session"),
        blank=True,
        null=True,
        help_text=_("Source pumping session. Leave blank for donor milk, "
                     "hand expression not logged, or prepared formula."),
    )
    type = models.CharField(
        blank=False,
        default="breast_milk",
        max_length=30,
        choices=[
            ("breast_milk", _("Breast milk")),
            ("donor_milk", _("Donor milk")),
        ],
        verbose_name=_("Type"),
        help_text=_("What type of feed is stored."),
    )
    amount = models.FloatField(
        blank=False, null=False, verbose_name=_("Amount")
    )
    amount_unit = models.CharField(
        blank=True,
        default="ml",
        max_length=5,
        choices=[("ml", _("ml")), ("oz", _("oz"))],
        verbose_name=_("Amount unit"),
    )
    amount_normalized = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Amount (normalized)"),
    )
    amount_remaining = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Amount remaining"),
        help_text=_(
            "Live remaining amount (ml). Decremented by consumption and "
            "discard events. Defaults to amount_normalized on creation."
        ),
    )
    storage_location = models.CharField(
        blank=False,
        default="room_temp",
        max_length=20,
        choices=[
            ("room_temp", _("Room temperature")),
            ("fridge", _("Refrigerator")),
            ("freezer", _("Freezer")),
            ("deep_freeze", _("Deep freezer")),
            ("cooler", _("Cooler (ice pack)")),
        ],
        verbose_name=_("Storage location"),
    )
    status = models.CharField(
        blank=False,
        default="fresh",
        max_length=20,
        choices=[
            ("fresh", _("Fresh")),
            ("frozen", _("Frozen")),
            ("thawed", _("Thawed")),
            ("used", _("Used")),
            ("discarded", _("Discarded")),
        ],
        verbose_name=_("Status"),
    )
    expressed_at = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Expressed at"),
        help_text=_(
            "When the milk was expressed (or formula prepared). Anchors "
            "the never-refrigerated room-temp and fridge use-by clocks."
        ),
    )
    fridge_entered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fridge entered at"),
        help_text=_("When the unit entered the refrigerator."),
    )
    freezer_entered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Freezer entered at"),
        help_text=_(
            "First freeze. Anchors the frozen 6-12 month quality clock "
            "(CDC: frozen age counts from first freeze)."
        ),
    )
    thaw_started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Thaw started at"),
    )
    thaw_completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Thaw completed at"),
        help_text=_("Anchors the thawed 24-hour fridge clock."),
    )
    warmed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Warmed at"),
        help_text=_(
            "First warming for feeding. Warming does not restart the "
            "room-temp window; use-by binds to the earlier anchor."
        ),
    )
    room_temp_since = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Room temp since"),
        help_text=_(
            "Start of the CURRENT room-temp stint, from any prior state "
            "(fridge/freezer exit or counter after expression). Null "
            "while the unit has never left cold storage; cleared and "
            "logged on return to cold storage."
        ),
    )
    cooler_entered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Cooler entered at"),
        help_text=_("Start of the current cooler stint (15C, 24h bound)."),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    label = models.CharField(
        blank=True,
        null=True,
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name=_("Label"),
        help_text=_(
            "Short write-on-the-cap ID (YYMMDD-NN). Assigned at "
            "creation; unique household-wide."
        ),
    )
    tags = TaggableManager(blank=True, through=Tagged)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-expressed_at"]
        verbose_name = _("Milk Inventory")
        verbose_name_plural = _("Milk Inventory")

    def __str__(self):
        label = self.label or ("#%d" % self.pk) if self.pk else "#?"
        return f"{label} · {self.amount_remaining or self.amount or 0:g} {self.amount_unit} {self.get_type_display()}"

    def _next_label(self):
        """YYMMDD-NN assigned per expression-day, seq reset daily."""
        # Household tz, not ambient tz: labels must follow the user's
        # configured timezone even when created outside web requests
        # (sync shell, token-auth API) where middleware never activates
        # it. See issue #36.
        day = to_household(self.expressed_at or timezone.now())
        prefix = day.strftime("%y%m%d") + "-"
        last = (
            FeedInventory.objects.filter(label__startswith=prefix)
            .order_by("-label")
            .values_list("label", flat=True)
            .first()
        )
        n = 1
        if last:
            try:
                n = int(last.rsplit("-", 1)[1]) + 1
            except (IndexError, ValueError):
                n = 1
        candidate = f"{prefix}{n:02d}"
        while FeedInventory.objects.filter(label=candidate).exists():
            n += 1
            candidate = f"{prefix}{n:02d}"
        return candidate

    def save(self, *args, **kwargs):
        """Normalize amount to ml and initialize amount_remaining."""
        if self.pk is None and not self.label:
            self.label = self._next_label()
        if self.amount is not None:
            if self.amount_unit == "oz":
                self.amount_normalized = round(self.amount * 29.5735, 2)
            else:
                self.amount_normalized = self.amount
            if self.amount_remaining is None:
                self.amount_remaining = self.amount_normalized
        if self.pk is None:
            # Creation: initialize the stint/clock field matching the
            # initial location. A unit that starts life on the counter
            # starts its room-temp stint at expression; a unit created
            # straight into cold storage never had one.
            anchor = self.expressed_at or timezone.now()
            if self.storage_location == "room_temp":
                if self.room_temp_since is None:
                    self.room_temp_since = anchor
            elif self.storage_location == "fridge":
                if self.fridge_entered_at is None:
                    self.fridge_entered_at = anchor
            elif self.storage_location in ("freezer", "deep_freeze"):
                if self.freezer_entered_at is None:
                    self.freezer_entered_at = anchor
                if self.status not in ("used", "discarded"):
                    self.status = "frozen"
            elif self.storage_location == "cooler":
                if self.cooler_entered_at is None:
                    self.cooler_entered_at = anchor
        super().save(*args, **kwargs)

    # ------------------------------------------------------------------
    # Status derivation + event ledger
    # ------------------------------------------------------------------

    @staticmethod
    def derive_status(source_status, destination):
        """Derive physical status after a location change.

        Convention (DECIDED 2026-08-17): status ALWAYS reflects the
        current physical state, never history — fresh milk moved to a
        freezer is "frozen", not "fresh". History lives in the
        event-timestamp fieldset and the FeedInventoryEvent ledger.
        """
        if destination in ("freezer", "deep_freeze"):
            # Entering (or staying in) a freezer: physically frozen.
            return "frozen"
        if source_status in ("frozen", "thawed"):
            # Leaving a freezer starts a thaw; thawed never returns to
            # fresh. Room temp, fridge and cooler are all "not frozen".
            return "thawed"
        return "fresh"

    #: Timestamp fields that carry the storage-history clocks. Shared by
    #: the ledger snapshot, combine min-merge, and transition engine.
    CLOCK_FIELDS = (
        "fridge_entered_at",
        "freezer_entered_at",
        "thaw_started_at",
        "thaw_completed_at",
        "warmed_at",
        "room_temp_since",
        "cooler_entered_at",
    )

    def clock_snapshot(self):
        """Current values of all storage-history clock fields."""
        return {field: getattr(self, field) for field in self.CLOCK_FIELDS}

    def mark_warmed(self, *, warmed_at, user=None):
        """B2 (2026-08-21): one-way 'this unit has been warmed' action.

        Sets warmed_at (only if unset), engages the existing cold-return
        guard + 2h clock. Never clears — warming is one-way.
        """
        if self.status in ("used", "discarded"):
            raise ValidationError(
                _("Cannot warm a used or discarded unit.")
            )
        if self.warmed_at is not None:
            raise ValidationError(
                _("This unit is already marked as warmed.")
            )
        self.warmed_at = warmed_at
        self.save(update_fields=["warmed_at"])
        self.record_event(
            "warmed",
            note="Marked warmed by {}".format(
                user.username if user else "system"
            ),
        )

    def record_event(self, event_type, amount_delta=None, feeding=None,
                     pumping=None, counterpart=None, note=""):
        """Append a ledger event snapshotting the unit's current state.

        Call AFTER mutating in-memory fields so the snapshot reflects the
        post-mutation state. Creates the FeedInventoryEvent row directly;
        no signals, no recursion.
        """
        return FeedInventoryEvent.objects.create(
            inventory=self,
            type=event_type,
            amount_delta=amount_delta,
            feeding=feeding,
            pumping=pumping,
            counterpart_unit=counterpart,
            remaining_after=self.amount_remaining,
            status=self.status,
            location=self.storage_location,
            expressed_at=self.expressed_at,
            fridge_entered_at=self.fridge_entered_at,
            freezer_entered_at=self.freezer_entered_at,
            thaw_started_at=self.thaw_started_at,
            thaw_completed_at=self.thaw_completed_at,
            warmed_at=self.warmed_at,
            room_temp_since=self.room_temp_since,
            cooler_entered_at=self.cooler_entered_at,
            note=note or "",
        )

    def _transition_mutate(self, new_location, at):
        """In-memory state mutation for a location change; no DB work.

        Returns (old_location, old_status, event_types). Shared by
        apply_transition() and the update view (which saves via the
        form). Call record-side effects only AFTER the unit is saved so
        ledger snapshots reflect post-mutation state.
        """
        events = []
        old_location = self.storage_location
        old_status = self.status

        self.storage_location = new_location
        self.status = self.derive_status(old_status, new_location)

        if new_location in ("freezer", "deep_freeze"):
            if self.thaw_started_at is not None or "thawed" in (
                old_status,
                self.status,
            ):
                raise ValidationError(
                    _(
                        "Thawed milk cannot be refrozen (CDC: never "
                        "refreeze breast milk after it has thawed). "
                        "Move it to the fridge and use within the "
                        "thawed window, or discard it."
                    )
                )
            if self.freezer_entered_at is None:
                self.freezer_entered_at = at
            if self.room_temp_since is not None:
                self.room_temp_since = None
                events.append("returned_to_cold_storage")
            if self.cooler_entered_at is not None:
                self.cooler_entered_at = None
                events.append("returned_to_cold_storage")
        elif new_location == "fridge":
            if self.fridge_entered_at is None:
                self.fridge_entered_at = at
            if old_status == "frozen":
                # Leaving the freezer for the fridge: thaw begins.
                if self.thaw_started_at is None:
                    self.thaw_started_at = at
            if self.room_temp_since is not None:
                self.room_temp_since = None
                events.append("returned_to_cold_storage")
            if self.cooler_entered_at is not None:
                self.cooler_entered_at = None
                events.append("returned_to_cold_storage")
        elif new_location == "room_temp":
            if self.room_temp_since is None:
                self.room_temp_since = at
                events.append("room_temp_stint_started")
            if old_status == "frozen":
                if self.thaw_started_at is None:
                    self.thaw_started_at = at
        elif new_location == "cooler":
            if self.cooler_entered_at is None:
                self.cooler_entered_at = at
                events.append("cooler_stint_started")

        return old_location, old_status, events

    def _write_transition_events(self, old_location, old_status, events,
                                 note=""):
        """Ledger writes for a completed transition (post-save)."""
        stint_events = [e for e in dict.fromkeys(events) if e != "status_changed"]
        if old_status != self.status:
            self.record_event(
                "status_changed",
                note=note
                or "Location {} → {} (status {} → {})".format(
                    old_location, self.storage_location, old_status, self.status
                ),
            )
        for event_type in stint_events:
            self.record_event(
                event_type,
                note="{} → {}".format(old_location, self.storage_location),
            )

    def apply_transition(self, new_location, at=None, note=""):
        """Apply a location change under the physical-state convention.

        Derives the new status, maintains the event-timestamp fieldset
        (stint starts, thaw anchors, first-freeze anchor), and writes the
        corresponding ledger events. Returns the list of event types
        written. By default this method saves the unit.

        Rules (docs/milk-inventory.md is the authoritative table):
        - freezer/deep_freeze: set freezer_entered_at if null (first
          freeze anchors the frozen clock; later re-entries keep the
          original), clear room-temp/cooler stints.
        - fridge: set fridge_entered_at if null; leaving a freezer starts
          a thaw (thaw_started_at if null); clear room-temp/cooler stints
          (return to cold storage is ledger-logged).
        - room_temp: set room_temp_since if null — start of the CURRENT
          stint only; prior counter time is never subtracted from a later
          window (CDC per-window semantics, DECIDED 2026-08-17).
        - cooler: set cooler_entered_at (own stint field, never touches
          room_temp_since and never resets any clock).
        """
        from django.db import transaction

        at = at or timezone.now()

        with transaction.atomic():
            old_location, old_status, events = self._transition_mutate(
                new_location, at
            )
            self.save()
            self._write_transition_events(old_location, old_status, events,
                                          note=note)
        return events

    # ------------------------------------------------------------------
    # Combine v2 (CDC-grounded rules, docs/milk-inventory.md)
    # ------------------------------------------------------------------

    #: Statuses that may participate in a combine as source or target.
    COMBINE_ELIGIBLE_STATUSES = ("fresh", "thawed")

    @staticmethod
    def combine_matrix(a_status, b_status):
        """Resulting status of combining two units; None = blocked.

        fresh+fresh → fresh; fresh+thawed (either direction) → thawed
        (most-perishable state wins, shortest clock); anything with
        frozen → blocked (can't merge frozen-solid bags); used/discarded
        are terminal and never combinable.
        """
        if a_status == "frozen" or b_status == "frozen":
            return None
        if a_status not in ("fresh", "thawed") or b_status not in ("fresh",
                                                                  "thawed"):
            return None
        return "thawed" if "thawed" in (a_status, b_status) else "fresh"

    def combine_into(self, others, at=None, keep_pumping_link=False):
        """Absorb other units into this one (combine v2).

        - Survivor: this unit (identity preserved); its status becomes
          the matrix result; clocks min-merge (Task 3 rules); expressed_at
          = oldest across all units.
        - Each absorbed unit: amount_remaining = 0, status = "used",
          pumping_session cleared (its lineage lives in the ledger), and
          ledger events combined_into (on the absorbed unit, snapshotting
          its full pre-merge state) + combined_from (on the survivor).
        - Guards are unconditional: frozen units (either side) never
          combine — physically impossible (fresh liquid cannot merge into
          a frozen solid; CDC rules forbid re-freezing after thaw).
          Thaw first, then combine.
        - keep_pumping_link=True: absorbed unit keeps its pumping_session
          FK so the lineage stays queryable on the unit itself.
        - Returns (merged_amount, [absorbed_units]).
        """
        from django.db import transaction

        at = at or timezone.now()
        others = list(others)
        if not others:
            return 0, []

        statuses = [self.status] + [o.status for o in others]
        if any(s == "frozen" for s in statuses):
            raise ValueError(_("Frozen units cannot be combined. Thaw first — CDC rules forbid re-freezing."))
        if any(s not in self.COMBINE_ELIGIBLE_STATUSES for s in statuses):
            raise ValueError(_("Only fresh or thawed units can be combined."))

        merged = 0.0
        with transaction.atomic():
            # ---- survivor takes min-merged clocks + oldest identity ----
            for field in ("expressed_at",) + self.CLOCK_FIELDS:
                vals = [getattr(o, field) for o in others]
                vals.append(getattr(self, field))
                own = getattr(self, field)
                non_null = [v for v in vals if v is not None]
                if non_null and (own is None or min(non_null) < own):
                    setattr(self, field, min(non_null))

            result_status = "thawed" if "thawed" in statuses else "fresh"
            self.status = result_status
            self.amount_remaining = round(
                (self.amount_remaining or 0)
                + sum(o.amount_remaining or 0 for o in others),
                2,
            )
            self.save()

            for o in others:
                o_amt = o.amount_remaining or 0
                merged += o_amt
                o.amount_remaining = 0
                o.status = "used"
                if not keep_pumping_link:
                    o.pumping_session = None
                o.save()
                o.record_event(
                    "combined_into",
                    counterpart=self,
                    note="Combined into unit #{}".format(self.pk),
                )
                self.record_event(
                    "combined_from",
                    counterpart=o,
                    amount_delta=o_amt,
                    note="Absorbed unit #{} ({} ml)".format(o.pk, o_amt),
                )
        return merged, others

    # ------------------------------------------------------------------
    # Use-by engine (derived, never stored). docs/milk-inventory.md is
    # the authoritative table. Dual thresholds = CDC numbers with ABM
    # Protocol #8 Table 1 granularity (optimal / acceptable); flat
    # single-tier windows where only one bound is evidenced.
    # ------------------------------------------------------------------

    RT_NEVER_COLD_OPTIMAL = timezone.timedelta(hours=4)
    RT_NEVER_COLD_ACCEPTABLE = timezone.timedelta(hours=8)
    RT_POST_COLD_WINDOW = timezone.timedelta(hours=2)
    FRIDGE_OPTIMAL = timezone.timedelta(days=4)
    FRIDGE_ACCEPTABLE = timezone.timedelta(days=8)
    THAWED_FRIDGE_WINDOW = timezone.timedelta(hours=24)
    COOLER_WINDOW = timezone.timedelta(hours=24)
    LEFTOVER_WINDOW = timezone.timedelta(hours=2)

    @staticmethod
    def _add_months(dt, months):
        try:
            from dateutil.relativedelta import relativedelta

            return dt + relativedelta(months=months)
        except ImportError:
            return dt + timezone.timedelta(days=round(30.44 * months))

    @staticmethod
    def _humanize_delta(td):
        """Compact positive-delta text: '45m', '3h 12m', '2d 5h', '7mo 4d'."""
        minutes = int(td.total_seconds() // 60)
        if minutes < 60:
            return "{}m".format(minutes)
        hours = minutes // 60
        if hours < 48:
            return "{}h {}m".format(hours, minutes % 60)
        days = hours // 24
        if days < 60:
            return "{}d {}h".format(days, hours % 24)
        months = int(days // 30.44)
        return "{}mo {}d".format(months, days - int(months * 30.44))

    def _core_use_by(self):
        """State clock: (label, two_tier, hard_bounds).

        two_tier is (optimal_at, acceptable_at) or None. hard_bounds is
        a list of (bound_dt, window_td) pairs for single-tier states;
        multi-clock states min-merge here already.
        """
        loc = self.storage_location
        st = self.status
        never_cold = (
            self.fridge_entered_at is None and self.freezer_entered_at is None
        )

        if st == "frozen":
            anchor = self.freezer_entered_at or self.expressed_at
            two = (
                self._add_months(anchor, 6),
                self._add_months(anchor, 12),
            )
            hard = []
            label = _("Frozen quality clock — from first freeze (CDC 6–12 mo)")
            if loc == "cooler" and self.cooler_entered_at:
                hard.append(
                    (self.cooler_entered_at + self.COOLER_WINDOW,
                     self.COOLER_WINDOW)
                )
                label = _("Frozen in cooler — transport, still icy")
            return label, two, hard

        if st == "thawed":
            thaw_anchor = (
                self.thaw_completed_at
                or self.thaw_started_at
                or self.expressed_at
            )
            if loc == "fridge":
                return (
                    _("Thawed — use within 24 h (fridge)"),
                    None,
                    [(thaw_anchor + self.THAWED_FRIDGE_WINDOW,
                      self.THAWED_FRIDGE_WINDOW)],
                )
            if loc == "cooler":
                hard = [(thaw_anchor + self.THAWED_FRIDGE_WINDOW,
                         self.THAWED_FRIDGE_WINDOW)]
                if self.cooler_entered_at:
                    hard.append(
                        (self.cooler_entered_at + self.COOLER_WINDOW,
                         self.COOLER_WINDOW)
                    )
                return (
                    _("Thawed in cooler — use ASAP (no tested bound)"),
                    None,
                    hard,
                )
            anchors = [
                t
                for t in (
                    self.thaw_completed_at,
                    self.thaw_started_at,
                    self.room_temp_since,
                    self.warmed_at,
                )
                if t is not None
            ]
            anchor = min(anchors) if anchors else self.expressed_at
            return (
                _("Thawed at room temp — 2 h window"),
                None,
                [(anchor + self.RT_POST_COLD_WINDOW, self.RT_POST_COLD_WINDOW)],
            )

        # fresh
        if loc == "fridge":
            return (
                _("Fridge storage — clock runs from expression"),
                (self.expressed_at + self.FRIDGE_OPTIMAL,
                 self.expressed_at + self.FRIDGE_ACCEPTABLE),
                [],
            )
        if loc == "cooler":
            hard = []
            if self.cooler_entered_at:
                hard.append(
                    (self.cooler_entered_at + self.COOLER_WINDOW,
                     self.COOLER_WINDOW)
                )
            if not never_cold:
                # Fridge clock keeps running during the cooler stint —
                # take its optimal (earlier) tier: conservative.
                hard.append(
                    (self.expressed_at + self.FRIDGE_OPTIMAL,
                     self.FRIDGE_OPTIMAL)
                )
            if not hard:
                return None
            return (
                _("Cooler — flat 24 h window (ABM/Hamosh 15 °C)"),
                None,
                hard,
            )
        if loc in ("freezer", "deep_freeze"):
            # Data oddity (fresh status inside a freezer): treat as the
            # physical state, frozen.
            anchor = self.freezer_entered_at or self.expressed_at
            return (
                _("Frozen quality clock — from first freeze (CDC 6–12 mo)"),
                (self._add_months(anchor, 6), self._add_months(anchor, 12)),
                [],
            )
        # room_temp
        if never_cold:
            return (
                _("Fresh on counter — never refrigerated"),
                (self.expressed_at + self.RT_NEVER_COLD_OPTIMAL,
                 self.expressed_at + self.RT_NEVER_COLD_ACCEPTABLE),
                [],
            )
        anchors = [self.room_temp_since or self.expressed_at]
        if self.warmed_at:
            anchors.append(self.warmed_at)
        return (
            _("Room temp after refrigeration — 2 h window"),
            None,
            [(min(anchors) + self.RT_POST_COLD_WINDOW, self.RT_POST_COLD_WINDOW)],
        )

    def use_by_info(self, now=None):
        """Derived use-by badge info; None when no window applies.

        Leftover rule (CDC FAQ): use within 2 h after the baby finishes
        feeding — min-merged into the hard bounds, conservative.
        """
        now = now or timezone.now()
        if self.status in ("used", "discarded"):
            return None
        core = self._core_use_by()
        if core is None:
            return None
        label, two, hard = core

        last_feed = None
        for feeding in self.feedings.all():
            if feeding.end and (last_feed is None or feeding.end > last_feed):
                last_feed = feeding.end
        if last_feed is not None:
            hard = list(hard) + [
                (last_feed + self.LEFTOVER_WINDOW, self.LEFTOVER_WINDOW)
            ]

        if two is not None and hard:
            earliest_hard = min(hard)[0]
            if earliest_hard < two[0]:
                # A hard bound (cooler/leftover) bites before the
                # optimal tier — flatten to a single-tier badge.
                two = None
                hard = [min(hard)]
            else:
                hard = [(min(two[1], min(hard)[0]), min(hard)[1])]

        if two is not None:
            optimal, acceptable = two
            # Display datetimes are localized to the household tz at the
            # emission point so badges/tooltips show the user's wall
            # clock even outside web requests (issue #36). All window
            # comparisons above run on aware datetimes and are tz-safe.
            optimal, acceptable = to_household(optimal), to_household(acceptable)
            if now >= acceptable:
                return {
                    "state_label": str(label),
                    "tier": "two_tier",
                    "optimal_at": optimal,
                    "acceptable_at": acceptable,
                    "bound_at": None,
                    "primary_text": _("Expired {} ago").format(
                        self._humanize_delta(now - acceptable)
                    ),
                    "secondary_text": "",
                    "css_class": "text-bg-danger",
                }
            if now >= optimal:
                return {
                    "state_label": str(label),
                    "tier": "two_tier",
                    "optimal_at": optimal,
                    "acceptable_at": acceptable,
                    "bound_at": None,
                    "primary_text": _("Use within {}").format(
                        self._humanize_delta(acceptable - now)
                    ),
                    "secondary_text": _("past optimal — acceptable window"),
                    "css_class": "text-bg-warning",
                }
            return {
                "state_label": str(label),
                "tier": "two_tier",
                "optimal_at": optimal,
                "acceptable_at": acceptable,
                "bound_at": None,
                "primary_text": self._humanize_delta(optimal - now),
                "secondary_text": _("acceptable: {}").format(
                    self._humanize_delta(acceptable - now)
                ),
                "css_class": "text-bg-success",
            }

        if not hard:
            return None
        bound, window = min(hard)
        remaining = bound - now
        info = {
            "state_label": str(label),
            "tier": "single",
            "optimal_at": None,
            "acceptable_at": None,
            "bound_at": to_household(bound),
            "css_class": "text-bg-success",
        }
        if remaining <= timezone.timedelta(0):
            info.update(
                primary_text=_("Expired {} ago").format(
                    self._humanize_delta(-remaining)
                ),
                secondary_text="",
                css_class="text-bg-danger",
            )
        else:
            fraction = remaining / window if window else timezone.timedelta(0)
            if fraction < 0.05:
                css = "text-bg-danger"
            elif fraction < 0.25:
                css = "text-bg-warning"
            else:
                css = "text-bg-success"
            info.update(
                primary_text=self._humanize_delta(remaining),
                secondary_text="",
                css_class=css,
            )
        return info

    def use_by_tooltip(self, now=None):
        """Plain-text explainer for the use-by badge (option C hybrid).

        Generated from the same engine output as the badge itself, so
        the numbers can never drift. Rendered as a Bootstrap tooltip
        title — plain text only, no markup.
        """
        info = self.use_by_info(now=now)
        if info is None:
            return ""
        parts = [info["state_label"] + "."]
        fmt = "%b %d %H:%M"
        if info["tier"] == "two_tier":
            if info["css_class"] == "text-bg-danger":
                parts.append(
                    _("Acceptable window passed — discard the milk.")
                )
            else:
                parts.append(
                    _("Optimal until {opt} (CDC guidance); acceptable "
                      "until {acc} (ABM research — quality declines "
                      "slowly, still safe).").format(
                        opt=info["optimal_at"].strftime(fmt),
                        acc=info["acceptable_at"].strftime(fmt),
                    )
                )
        else:
            bound = info.get("bound_at")
            if info["css_class"] == "text-bg-danger":
                parts.append(_("Window passed — discard the milk."))
            elif bound is not None:
                parts.append(
                    _("Use by {bound} — hard limit for this storage "
                      "state.").format(bound=bound.strftime(fmt))
                )
        return " ".join(str(p) for p in parts)

    def clean(self):
        """Physical-state invariants (2026-08-17, user ruling).

        A warmed-but-unfed unit must not go back into cold storage:
        once a bottle has been warmed, CDC-conservative policy treats it
        as on a one-way 2h clock — no fridge return, no re-freeze.
        The transition engine already never sets warmed_at (there is no UI
        to warm a unit today), so this guard is protective: it fires if
        a warmed unit (via admin or a future warmer feature) is moved
        to fridge/freezer/deep_freeze by edit.
        """
        if self.warmed_at and self.storage_location in (
            "fridge",
            "freezer",
            "deep_freeze",
        ):
            raise ValidationError(
                _(
                    "This unit has been warmed (warmed_at is set) — it "
                    "cannot return to cold storage. CDC-conservative "
                    "rule: warmed milk stays on its 2-hour clock (use "
                    "or discard)."
                )
            )
        # Refreeze block (CDC, 2026-08-21): thawed milk never goes back
        # into a freezer. thaw_started_at is the durable signal; status
        # "thawed" catches legacy rows that predate the anchor field.
        if self.storage_location in ("freezer", "deep_freeze") and (
            self.thaw_started_at is not None or self.status == "thawed"
        ):
            raise ValidationError(
                _(
                    "Thawed milk cannot be refrozen (CDC: never refreeze "
                    "breast milk after it has thawed). Use it within the "
                    "thawed window or discard it."
                )
            )


class FeedInventoryEvent(models.Model):
    """
    Append-only ledger for every mutation of a FeedInventory unit.

    One row per event with a full snapshot of the unit's post-event state
    (amount remaining, status, location, and the complete event-timestamp
    fieldset). Combine events snapshot every clock field of the absorbed
    unit so pre-merge history stays reconstructible from the ledger alone.

    No edits, no deletes from user code; the ledger starts at deploy and
    is never backfilled.
    """

    model_name = "feed_inventory_event"

    EVENT_TYPES = [
        ("created_from_pumping", _("Created from pumping")),
        ("feeding_consumed", _("Consumed by feeding")),
        ("feeding_restored", _("Restored (feeding edit/unlink)")),
        ("consume_manual", _("Manual consume")),
        ("combined_into", _("Combined into another unit")),
        ("combined_from", _("Absorbed another unit")),
        ("split_off", _("Split off from this unit")),
        ("split_to", _("Split into this unit")),
        ("discarded", _("Discarded")),
        ("status_changed", _("Status changed")),
        ("room_temp_stint_started", _("Room temp stint started")),
        ("cooler_stint_started", _("Cooler stint started")),
        ("returned_to_cold_storage", _("Returned to cold storage")),
    ]

    inventory = models.ForeignKey(
        "FeedInventory",
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Inventory unit"),
    )
    feeding = models.ForeignKey(
        "Feeding",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="feed_inventory_events",
        verbose_name=_("Feeding"),
        help_text=_("Feeding that caused this event, if any."),
    )
    pumping = models.ForeignKey(
        "Pumping",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="feed_inventory_events",
        verbose_name=_("Pumping"),
        help_text=_("Pumping session that caused this event, if any."),
    )
    counterpart_unit = models.ForeignKey(
        "FeedInventory",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="counterpart_events",
        verbose_name=_("Counterpart unit"),
        help_text=_("Other unit involved (combine/split partner)."),
    )
    type = models.CharField(
        blank=False,
        max_length=32,
        choices=EVENT_TYPES,
        verbose_name=_("Event type"),
    )
    amount_delta = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Amount delta"),
        help_text=_("Change to amount_remaining in ml (+/-)."),
    )
    remaining_after = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Remaining after"),
    )
    status = models.CharField(
        blank=True,
        max_length=20,
        verbose_name=_("Status snapshot"),
    )
    location = models.CharField(
        blank=True,
        max_length=20,
        verbose_name=_("Location snapshot"),
    )
    # Full event-timestamp fieldset snapshot.
    expressed_at = models.DateTimeField(blank=True, null=True)
    fridge_entered_at = models.DateTimeField(blank=True, null=True)
    freezer_entered_at = models.DateTimeField(blank=True, null=True)
    thaw_started_at = models.DateTimeField(blank=True, null=True)
    thaw_completed_at = models.DateTimeField(blank=True, null=True)
    warmed_at = models.DateTimeField(blank=True, null=True)
    room_temp_since = models.DateTimeField(blank=True, null=True)
    cooler_entered_at = models.DateTimeField(blank=True, null=True)
    note = models.CharField(blank=True, default="", max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view",)
        ordering = ["-created_at"]
        verbose_name = _("Milk Inventory Event")
        verbose_name_plural = _("Milk Inventory Events")

    def __str__(self):
        return "{type} — #{pk} {delta} → {rem} ml".format(
            type=self.get_type_display(),
            pk=self.inventory_id,
            delta="{:+g}".format(self.amount_delta)
            if self.amount_delta is not None
            else "±0",
            rem=self.remaining_after if self.remaining_after is not None else "?",
        )


class DoctorVisit(models.Model):
    """
    A record of a doctor's visit for a child, tracking appointment details,
    diagnosis, and follow-up actions.
    """

    model_name = "doctorvisit"

    APPOINTMENT_TYPE_CHOICES = [
        ("well_visit", _("Well Visit")),
        ("sick_visit", _("Sick Visit")),
        ("lactation_consultant", _("Lactation Consultant")),
        ("specialist", _("Specialist")),
        ("er", _("ER / Urgent Care")),
        ("other", _("Other")),
    ]

    child = models.ForeignKey(
        "Child",
        on_delete=models.CASCADE,
        related_name="doctor_visits",
        verbose_name=_("Child"),
    )
    date_time = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Date/Time"),
    )
    appointment_type = models.CharField(
        max_length=32,
        choices=APPOINTMENT_TYPE_CHOICES,
        blank=False,
        verbose_name=_("Appointment Type"),
    )
    doctor_name = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Doctor Name"),
    )
    practice = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Practice / Clinic"),
    )
    reason = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Reason"),
        help_text=_("Why are we going?"),
    )
    symptoms_notes = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Symptoms / Questions"),
        help_text=_("Questions for the doctor"),
    )
    diagnosis = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Diagnosis / Findings"),
    )
    action_items = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Follow-up / Action Items"),
        help_text=_("Follow-up tasks, referrals, next steps"),
    )
    weight_measured = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Weight Measured (kg)"),
        help_text=_("Weight at visit in kg"),
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Notes"),
    )

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-date_time"]
        verbose_name = _("Doctor Visit")
        verbose_name_plural = _("Doctor Visits")

    def __str__(self):
        date_str = (
            to_household(self.date_time).strftime("%Y-%m-%d")
            if self.date_time
            else ""
        )
        doctor = self.doctor_name or ""
        reason = self.reason or self.get_appointment_type_display() or ""
        parts = [s for s in [date_str, doctor, reason] if s]
        return " — ".join(parts) if parts else str(_("Doctor Visit"))

class InventoryTransaction(models.Model):
    """Immutable audit log for every change to a pool's quantity."""
    model_name = "inventory_transaction"

    TRANSACTION_TYPES = [
        ("initial", _("Pool created")),
        ("decrement", _("Diaper change")),
        ("restore", _("Change deleted")),
        ("adjustment", _("Manual adjust / count")),
        ("recalc", _("Recalculate")),
    ]

    supply_item = models.ForeignKey(
        "SupplyItem",
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Supply item"),
    )
    delta = models.IntegerField(
        verbose_name=_("Delta"),
        help_text=_("+1 = increment, -1 = decrement, etc."),
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES,
        verbose_name=_("Type"),
    )
    source_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("Source ID"),
        help_text=_("DiaperChange PK or InventoryAdjustment PK."),
    )
    quantity_after = models.IntegerField(
        verbose_name=_("Quantity after"),
        help_text=_("Pool's quantity after this transaction."),
    )
    note = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Note"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view",)
        ordering = ["-created_at"]
        verbose_name = _("Inventory Transaction")
        verbose_name_plural = _("Inventory Transactions")

    def __str__(self):
        sign = "+" if self.delta >= 0 else ""
        return f"{self.created_at:%Y-%m-%d %H:%M} — {sign}{self.delta} ({self.transaction_type}) → {self.quantity_after}"

class InventoryAdjustment(models.Model):
    """A correction to a pool's quantity at a point in time.

    Recalc uses the most recent adjustment as the anchor baseline:
    quantity = adjustment.physical_count - changes_since(adjustment.count_time).
    """
    model_name = "inventory_adjustment"

    ADJUSTMENT_TYPES = [
        ("manual_adjust", _("Manual adjust")),
        ("snapshot_brand", _("Physical count — brand-specific")),
        ("snapshot_size_only", _("Physical count — size-only")),
    ]

    supply_item = models.ForeignKey(
        "SupplyItem",
        on_delete=models.CASCADE,
        related_name="adjustments",
        verbose_name=_("Supply item"),
    )
    count_time = models.DateTimeField(
        verbose_name=_("Count time"),
        help_text=_("When this count was taken."),
    )
    physical_count = models.IntegerField(
        verbose_name=_("Physical count"),
        help_text=_("Number of items physically on hand at count time."),
    )
    reason = models.CharField(
        blank=True,
        default="",
        max_length=255,
        verbose_name=_("Reason"),
    )
    adjustment_type = models.CharField(
        max_length=20,
        choices=ADJUSTMENT_TYPES,
        default="manual_adjust",
        verbose_name=_("Type"),
    )
    session_id = models.CharField(
        blank=True,
        default="",
        max_length=36,
        verbose_name=_("Session ID"),
        help_text=_("UUID grouping multiple adjustments from one count session."),
    )
    system_count_before = models.IntegerField(
        default=0,
        verbose_name=_("System count before"),
        help_text=_("What the system thought the count was before this adjustment."),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-count_time"]
        verbose_name = _("Inventory Adjustment")
        verbose_name_plural = _("Inventory Adjustments")

    def __str__(self):
        return f"{self.count_time:%Y-%m-%d %H:%M} — {self.physical_count}ct ({self.adjustment_type})"



class FormulaStock(SyncTimestampMixin, models.Model):
    """
    Purchase-level formula container stock (powder cans, sealed RTF
    bottles/jugs). Household-scoped — no child FK (mirrors the milk
    inventory household-pool decision).

    A row is EITHER a pool of identical sealed containers (quantity >= 1,
    opened_at null) OR exactly one opened container (opened_at set,
    quantity locked to 1, grams_remaining/ml_remaining live).

    Powder use-by (CDC): opened -> min(expiry_date, opened_at + 1 month);
    store cool/dry, never refrigerate. Sealed -> expiry only.
    RTF (DECISION #1): sealed -> shelf-stable, expiry only. Opened ->
    48h fridge use-by from open, <=1h room-temp stints, fridge returns
    allowed until the 48h cap.
    """

    model_name = "formula_stock"

    FORMS = [
        ("powder", _("Powder")),
        ("rtf", _("Ready-to-feed")),
    ]

    product_line = models.ForeignKey(
        ProductLine,
        on_delete=models.PROTECT,
        related_name="formula_stock",
        verbose_name=_("Product"),
        limit_choices_to={"item_type": "formula"},
    )
    form = models.CharField(
        blank=False,
        default="powder",
        max_length=10,
        choices=FORMS,
        verbose_name=_("Form"),
    )
    container_size = models.FloatField(
        blank=False,
        null=False,
        verbose_name=_("Container size"),
        help_text=_(
            "Powder: grams per full container. Ready-to-feed: ml per "
            "full container."
        ),
    )
    quantity = models.IntegerField(
        default=1,
        verbose_name=_("Sealed containers"),
        help_text=_(
            "Count of identical sealed containers in this pool. Must be "
            "1 (locked) once a container from this pool is opened."
        ),
    )
    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Expiry date"),
    )
    opened_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Opened at"),
        help_text=_(
            "Set means this row is exactly ONE opened container "
            "(quantity locked to 1)."
        ),
    )
    grams_remaining = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Grams remaining"),
        help_text=_("Powder rows only: live grams in the opened can."),
    )
    ml_remaining = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("ml remaining"),
        help_text=_("Ready-to-feed rows only: live ml in the opened container."),
    )
    acquisition_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Acquisition date"),
    )
    usage_eligible = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Usage eligible from"),
        help_text=_(
            "Date/time from which this pool may be decremented. Leave "
            "null for sealed/reserve stock that should not be touched."
        ),
    )
    drain_priority = models.IntegerField(
        default=0,
        verbose_name=_("Drain priority"),
        help_text=_(
            "Higher = drained first. 0 = normal (FIFO by usage_eligible)."
        ),
    )
    is_reserve = models.BooleanField(
        default=False,
        verbose_name=_("Reserve stock"),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    objects = models.Manager()
    settings = FormulaClockSettings(_("Formula clock settings"))

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = [
            "is_reserve",
            "-drain_priority",
            "product_line__brand",
            "product_line__line",
            "-opened_at",
        ]
        verbose_name = _("Formula Stock")
        verbose_name_plural = _("Formula Stock")

    def __str__(self):
        label = str(self.product_line)
        if self.opened_at is not None:
            unit = "g" if self.form == "powder" else "ml"
            remaining = self.grams_remaining if self.form == "powder" else self.ml_remaining
            return f"{label} (opened, {remaining or 0:g} {unit} left)"
        return f"{label} (sealed x{self.quantity})"

    @property
    def is_open(self):
        return self.opened_at is not None

    def use_by(self):
        """
        Derived use-by bound (never stored). Returns an aware datetime,
        or None when no bound applies.

        - Sealed (either form): printed expiry only (shelf-stable).
        - Opened powder: min(expiry_date, opened_at + 1 month) — CDC.
        - Opened RTF: opened_at + 48h (fridge clock, DECISION #1); the
          <=1h room-temp stint rule is per-stint and rendered by the UI.
        """
        import datetime as _dt

        if self.opened_at is None:
            if self.expiry_date is None:
                return None
            return timezone.make_aware(
                _dt.datetime.combine(self.expiry_date, _dt.time.min)
            )
        if self.form == "powder":
            try:
                from dateutil.relativedelta import relativedelta

                days = FormulaStock.settings.powder_use_by_days
                bound = self.opened_at + relativedelta(days=days)
            except ImportError:
                bound = self.opened_at + timezone.timedelta(days=31)
            if self.expiry_date is not None:
                cap = timezone.make_aware(
                    _dt.datetime.combine(self.expiry_date, _dt.time.min)
                )
                bound = min(bound, cap)
            return bound
        return self.opened_at + timezone.timedelta(
            hours=FormulaStock.settings.rtf_use_by_hours
        )

    def clean(self):
        if self.opened_at is not None and self.quantity != 1:
            raise ValidationError(
                _(
                    "An opened-container row is exactly ONE container — "
                    "quantity must be 1."
                )
            )
        if self.form == "powder" and self.ml_remaining is not None:
            raise ValidationError(
                _("ml_remaining applies to ready-to-feed rows only.")
            )
        if self.form == "rtf" and self.grams_remaining is not None:
            raise ValidationError(_("grams_remaining applies to powder rows only."))

    # ------------------------------------------------------------------
    # T2: derived clock + open flow + drain order
    # ------------------------------------------------------------------

    #: Opened RTF use-by window (fridge clock, DECISION #1). The
    #: conservative 24h knob is a dbsettings candidate, not a constant
    #: flip - 48h is the Similac/Enfamil label default.
    RTF_FRIDGE_WINDOW = timezone.timedelta(hours=48)
    #: Max room-temp stint for an opened RTF container (per stint).
    RTF_RT_STINT = timezone.timedelta(hours=1)

    @staticmethod
    def _humanize_delta(delta):
        """Compact positive-delta text (matches FeedInventory's format)."""
        seconds = int(delta.total_seconds())
        if seconds < 0:
            seconds = -seconds
        minutes = seconds // 60
        if minutes < 60:
            return "{}m".format(minutes)
        hours = minutes // 60
        if hours < 48:
            return "{}h {}m".format(hours, minutes % 60)
        return "{}d {}h".format(hours // 24, hours % 24)


    def _state_label(self):
        if self.opened_at is None:
            return _("Sealed - shelf-stable")
        if self.form == "powder":
            return _("Opened powder - never refrigerate")
        return _("Opened RTF - refrigerate between uses")

    def use_by_info(self, now=None):
        """
        Badge info for the stock list (mirrors FeedInventory.use_by_info
        semantics: state label, primary text, css class, tooltip).

        Returns None when no window applies (sealed, no expiry).
        Single-tier only - formula has no two-tier (optimal/acceptable)
        windows; every bound is a hard CDC/label rule.
        """
        now = now or timezone.now()
        bound = self.use_by()
        if bound is None:
            return None

        info = {
            "state_label": self._state_label(),
            "tier": "single",
            # Display datetime localized to the household tz (issue #36):
            # badges must show the user's wall clock, not server UTC.
            "bound_at": to_household(bound),
            "secondary_text": "",
            "stint_warning": False,
        }

        if now >= bound:
            info.update(
                primary_text=_("Expired {} ago").format(
                    self._humanize_delta(now - bound)
                ),
                css_class="text-bg-danger",
            )
            return info

        remaining = bound - now
        info.update(
            primary_text=_("Use within {}").format(
                self._humanize_delta(remaining)
            ),
            css_class=(
                "text-bg-warning"
                if remaining <= timezone.timedelta(hours=48)
                else "text-bg-success"
            ),
            # Opened RTF carries the per-stint rule; surfaced as a
            # secondary hint, not a separate badge tier.
            stint_warning=bool(self.form == "rtf" and self.is_open),
        )
        return info

    @property
    def use_by_tooltip(self):
        info = self.use_by_info()
        if info is None:
            return ""
        parts = [str(info["state_label"]) + "."]
        fmt = "%b %d %H:%M"
        if info["css_class"] == "text-bg-danger":
            parts.append(_("Discard the contents."))
        else:
            parts.append(
                _("Bound: {bound}.").format(
                    bound=info["bound_at"].strftime(fmt)
                )
            )
        if self.opened_at is not None and self.form == "rtf":
            parts.append(
                _(
                    "Room-temp stints max 1 h per stint; return to the "
                    "fridge between pours until the 48 h cap."
                )
            )
        if self.opened_at is not None and self.form == "powder":
            parts.append(
                _("Store cool and dry - never refrigerate opened powder.")
            )
        return " ".join(str(p) for p in parts)

    @staticmethod
    def drain_ordered_opened_pools():
        """All opened rows in drain order, reserve last."""
        return FormulaStock.objects.filter(opened_at__isnull=False).order_by(
            "is_reserve", "-drain_priority", "opened_at", "usage_eligible"
        )

    def record_event(self, event_type, *, delta_grams=None, delta_ml=None,
                     grams_after=None, ml_after=None, source_id=None,
                     note=""):
        """Append-only ledger write (mirrors FeedInventory.record_event)."""
        return FormulaStockEvent.objects.create(
            stock=self,
            type=event_type,
            delta_grams=delta_grams,
            delta_ml=delta_ml,
            grams_after=grams_after,
            ml_after=ml_after,
            source_id=source_id,
            note=note,
        )

    def open_container(self, *, opened_at=None, user=None):
        """
        Open one sealed container from this pool (atomic).

        Pool.quantity > 1: decrement to pool.quantity - 1 and create a
        NEW row for the opened container (quantity=1, full remaining).
        Pool.quantity == 1: flip this row in place (opened_at set,
        remaining = container_size, usage_eligible set to now).

        Both directions write ledger 'opened' events and are audit-clean
        (pool side records the quantity delta; opened side records the
        initial remaining). Matches the spec's "two rows" semantics.
        """
        from django.db import transaction

        if self.opened_at is not None:
            raise ValidationError(
                _("This row is already an opened container.")
            )
        if self.quantity < 1:
            raise ValidationError(
                _("Cannot open - the pool is empty.")
            )

        opened_at = opened_at or timezone.now()

        with transaction.atomic():
            if self.quantity > 1:
                self.quantity -= 1
                self.save(update_fields=["quantity"])
                self.record_event(
                    "opened",
                    note="Sealed container opened from pool "
                    "(quantity {q} -> {q2})".format(
                        q=self.quantity + 1, q2=self.quantity
                    ),
                )
                opened_row = FormulaStock.objects.create(
                    product_line=self.product_line,
                    form=self.form,
                    container_size=self.container_size,
                    quantity=1,
                    expiry_date=self.expiry_date,
                    opened_at=opened_at,
                    grams_remaining=(
                        self.container_size
                        if self.form == "powder"
                        else None
                    ),
                    ml_remaining=(
                        self.container_size
                        if self.form == "rtf"
                        else None
                    ),
                    acquisition_date=self.acquisition_date,
                    drain_priority=self.drain_priority,
                    is_reserve=self.is_reserve,
                    usage_eligible=opened_at,
                    notes=self.notes,
                )
            else:
                opened_row = self
                opened_row.opened_at = opened_at
                if self.form == "powder":
                    opened_row.grams_remaining = self.container_size
                else:
                    opened_row.ml_remaining = self.container_size
                opened_row.usage_eligible = opened_at
                opened_row.save(
                    update_fields=[
                        "opened_at",
                        "grams_remaining",
                        "ml_remaining",
                        "usage_eligible",
                    ]
                )
            opened_row.record_event(
                "opened",
                delta_grams=(
                    opened_row.grams_remaining
                    if opened_row.form == "powder"
                    else None
                ),
                delta_ml=(
                    opened_row.ml_remaining
                    if opened_row.form == "rtf"
                    else None
                ),
                grams_after=opened_row.grams_remaining,
                ml_after=opened_row.ml_remaining,
                note="Container opened - clock started",
            )
        return opened_row


class PreparedFeed(models.Model):
    """
    A prepared bottle of formula (third entity — distinct from sealed
    stock pools and from stored milk units).

    Creation paths (DECISION #2): standalone prep logging AND
    create-at-first-feeding from the bottle-feeding form (T3/T4 build
    those flows). Clocks are DERIVED, never stored: room temp 2h from
    prep; 1h from feed start once feeding begins; fridge 24h; leftover
    = immediate discard at feed end (CDC formula rules — NO grace
    window; must not reuse milk's 2h leftover rule).

    source_inventory is RESERVED and unwired (DECISION #5): breast-milk
    bottles keep the shipped Feeding.feed_inventory flow.
    """

    model_name = "prepared_feed"

    PREPARED_FROM = [
        ("powder_mix", _("Mixed from powder")),
        ("rtf_pour", _("Poured from RTF")),
    ]
    STATUS = [
        ("active", _("Active")),
        ("consumed", _("Consumed")),
        ("discarded", _("Discarded")),
    ]

    source_pool = models.ForeignKey(
        FormulaStock,
        on_delete=models.SET_NULL,
        related_name="prepared_feeds",
        verbose_name=_("Source pool"),
        blank=True,
        null=True,
    )
    source_inventory = models.ForeignKey(
        "FeedInventory",
        on_delete=models.SET_NULL,
        related_name="prepared_feeds",
        verbose_name=_("Source milk unit"),
        blank=True,
        null=True,
        help_text=_(
            "RESERVED for future fortified/unified tracking — not wired."
        ),
    )
    prepared_from = models.CharField(
        blank=False,
        default="powder_mix",
        max_length=20,
        choices=PREPARED_FROM,
        verbose_name=_("Prepared from"),
    )
    amount = models.FloatField(
        blank=False,
        null=False,
        verbose_name=_("Amount prepared (ml)"),
    )
    amount_remaining = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Amount remaining (ml)"),
        help_text=_("Decremented by feedings; defaults to amount."),
    )
    grams_used = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Grams used"),
        help_text=_("Powder lineage: grams taken from the pool at prep."),
    )
    prepared_at = models.DateTimeField(
        blank=False,
        default=timezone.localtime,
        null=False,
        verbose_name=_("Prepared at"),
    )
    fridge_entered_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("Fridge entered at"),
    )
    first_fed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_("First fed at"),
    )
    status = models.CharField(
        blank=False,
        default="active",
        max_length=20,
        choices=STATUS,
        verbose_name=_("Status"),
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))

    objects = models.Manager()

    # CDC formula storage clocks (spec §System 2 — derived, never stored):
    # room temp 2h from prep; once feeding starts 1h from feed start;
    # fridge 24h from fridge entry. Leftover = immediate discard at feed
    # end — NO grace window (must not reuse milk's 2h leftover rule).
    ROOM_TEMP_WINDOW = timezone.timedelta(hours=2)
    FEEDING_WINDOW = timezone.timedelta(hours=1)
    FRIDGE_WINDOW = timezone.timedelta(hours=24)

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-prepared_at"]
        verbose_name = _("Prepared Feed")
        verbose_name_plural = _("Prepared Feeds")

    def __str__(self):
        return "#{} {} {} ml ({})".format(
            self.pk or "?",
            self.get_prepared_from_display(),
            self.amount_remaining if self.amount_remaining is not None else self.amount,
            self.get_status_display(),
        )

    def _clock_bound(self, now=None):
        """Earliest CDC bound for this unit: derived, never stored.

        - No fridge entry + feeding never started: room temp 2h from
          prep (treats prep→first feed as the start of the window).
        - No fridge entry + feeding started: 1h from first feed.
        - Fridge entry recorded: 24h from fridge entry.

        Returns (bound, reason_code) or (None, None) for terminal
        units (consumed/discarded — no live clock).
        """
        if self.status != "active":
            return (None, None)
        if self.fridge_entered_at is not None:
            return (self.fridge_entered_at + self.FRIDGE_WINDOW, "fridge")
        if self.first_fed_at is not None:
            return (self.first_fed_at + self.FEEDING_WINDOW, "feeding")
        return (self.prepared_at + self.ROOM_TEMP_WINDOW, "room_temp")

    def use_by_info(self, now=None):
        """Badge info for the prepared list (mirrors the sibling
        use_by_info semantics: state label, primary text, css class).

        Single-tier only — formula's bounds are all hard CDC rules;
        there is no optimal/acceptable split. None for terminal units.
        """
        now = now or timezone.now()
        bound, reason = self._clock_bound(now)
        if bound is None:
            return None

        state_labels = {
            "room_temp": _("Room temp - use within 2h of prep"),
            "feeding": _("Feeding started - use within 1h of feed start"),
            "fridge": _("Refrigerated - use within 24h of fridge entry"),
        }

        info = {
            "state_label": state_labels[reason],
            "tier": "single",
            "bound_at": to_household(bound),
            "secondary_text": "",
            "stint_warning": False,
        }

        if now >= bound:
            info.update(
                primary_text=_("Expired {} ago").format(
                    self._humanize_delta(now - bound)
                ),
                css_class="text-bg-danger",
            )
            return info

        remaining = bound - now
        info.update(
            primary_text=_("Use within {}").format(
                self._humanize_delta(remaining)
            ),
            css_class=(
                "text-bg-warning"
                if remaining <= timezone.timedelta(hours=1)
                else "text-bg-success"
            ),
        )
        return info

    @staticmethod
    def _humanize_delta(td):
        """Compact positive-delta text: '45m', '3h 12m' (matches the
        sibling models' badge format)."""
        minutes = int(td.total_seconds() // 60)
        if minutes < 1:
            return "<1m"
        if minutes < 60:
            return "{}m".format(minutes)
        hours = minutes // 60
        return "{}h {}m".format(hours, minutes % 60)

    @property
    def use_by_tooltip(self):
        info = self.use_by_info()
        if info is None:
            return ""
        parts = [str(info["state_label"]) + "."]
        if info["css_class"] == "text-bg-danger":
            parts.append(str(_("Discard the contents.")))
        else:
            parts.append(
                str(_("Use by {}.").format(
                    info["bound_at"].strftime("%b %d %H:%M")
                ))
            )
        return " ".join(parts)

    def record_event(self, event_type, *, delta_grams=None, delta_ml=None,
                     grams_after=None, ml_after=None, source_id=None,
                     note=""):
        """Append-only ledger write (mirrors FormulaStock.record_event,
        targeting this unit instead of a stock pool)."""
        return FormulaStockEvent.objects.create(
            prepared_feed=self,
            type=event_type,
            delta_grams=delta_grams,
            delta_ml=delta_ml,
            grams_after=grams_after,
            ml_after=ml_after,
            source_id=source_id,
            note=note,
        )

    def save(self, *args, **kwargs):
        if self.amount_remaining is None:
            self.amount_remaining = self.amount
        previous = None
        if self.pk:
            previous = PreparedFeed.objects.filter(pk=self.pk).first()
        # Powder mixes: derive grams_used from the pool's label ratio.
        # Create: default when absent. Edit (amount/pool changed):
        # recompute only when the stored value matches the OLD
        # derivation — a manual grams_used override survives edits.
        if self.prepared_from == "powder_mix" and self.source_pool_id:
            derived = Feeding._powder_grams(
                self.source_pool.product_line, self.amount
            )
            if self.grams_used is None:
                self.grams_used = derived
            elif previous is not None and (
                previous.amount != self.amount
                or previous.source_pool_id != self.source_pool_id
            ):
                old_line = (
                    previous.source_pool.product_line
                    if previous.source_pool_id
                    else self.source_pool.product_line
                )
                old_derived = Feeding._powder_grams(
                    old_line, previous.amount
                )
                if self.grams_used == old_derived:
                    self.grams_used = derived
        super().save(*args, **kwargs)
        self._adjust_source_pool(previous)

    def _pool_delta(self):
        """(kind, qty) this prep draws from its source pool."""
        if not self.source_pool_id or not self.amount:
            return (None, 0)
        if self.prepared_from == "rtf_pour":
            return ("ml", self.amount)
        return ("grams", self.grams_used or 0)

    def _adjust_source_pool(self, previous):
        """Restore-then-decrement the source pool at prep (ledger both
        directions; event types pre-provisioned by T1: prep_decrement /
        prep_restored / poured). Powder mixes decrement grams via the
        label ratio; RTF pours decrement ml directly.

        Pool effect keys off (source_pool, amount, grams_used) — status
        transitions do NOT touch the pool (the formula physically left
        the container at prep; consumed/discarded only closes the unit).
        """
        old_pool_id = previous.source_pool_id if previous else None
        new_pool_id = self.source_pool_id
        old_amount = previous.amount if previous else None
        old_grams = previous.grams_used if previous else None
        unchanged = (
            old_pool_id == new_pool_id
            and old_amount == self.amount
            and old_grams == self.grams_used
        )
        if unchanged:
            return

        if old_pool_id and previous is not None:
            kind, qty = previous._pool_delta()
            if qty:
                self._shift_pool(old_pool_id, kind, +qty, "prep_restored",
                                 "Prep edited - restored to source pool")

        kind, qty = self._pool_delta()
        if new_pool_id and qty:
            event = "poured" if kind == "ml" else "prep_decrement"
            self._shift_pool(new_pool_id, kind, -qty, event,
                             "Prep drew from source pool")

    @staticmethod
    def _shift_pool(pool_id, kind, qty, event, note):
        """Apply ±qty to a stock pool (clamped ≥ 0) + ledger write."""
        field = "ml_remaining" if kind == "ml" else "grams_remaining"
        FormulaStock.objects.filter(pk=pool_id).update(
            **{field: Greatest(0.0, F(field) + qty)}
        )
        stock = FormulaStock.objects.get(pk=pool_id)
        stock.record_event(
            event,
            delta_ml=qty if kind == "ml" else None,
            delta_grams=qty if kind == "grams" else None,
            grams_after=stock.grams_remaining,
            ml_after=stock.ml_remaining,
            note=note,
        )

    def clean(self):
        if self.source_inventory_id is not None:
            raise ValidationError(
                _(
                    "source_inventory is reserved for future unified "
                    "milk/formula tracking (DECISION #5) and is not "
                    "wired yet."
                )
            )
        if self.amount_remaining is not None and self.amount_remaining > self.amount:
            raise ValidationError(
                _("Amount remaining cannot exceed amount prepared.")
            )


class FormulaStockEvent(models.Model):
    """
    Append-only ledger for the whole formula side — pools AND prepared
    units (mirrors the shipped FeedInventoryEvent pattern). No edits,
    no deletes from user code; starts at deploy, never backfilled.
    """

    model_name = "formula_stock_event"

    EVENT_TYPES = [
        ("initial", _("Initial stock")),
        ("opened", _("Container opened")),
        ("feeding_decrement", _("Feeding decrement")),
        ("feeding_restored", _("Feeding restored (edit/unlink)")),
        ("prep_decrement", _("Prep decrement")),
        ("prep_restored", _("Prep restored (edit/delete)")),
        ("poured", _("Poured from RTF")),
        ("manual_adjust", _("Manual adjust")),
        ("discarded", _("Discarded")),
    ]

    stock = models.ForeignKey(
        FormulaStock,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Stock"),
        blank=True,
        null=True,
    )
    prepared_feed = models.ForeignKey(
        PreparedFeed,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name=_("Prepared feed"),
        blank=True,
        null=True,
    )
    type = models.CharField(
        blank=False,
        max_length=32,
        choices=EVENT_TYPES,
        verbose_name=_("Event type"),
    )
    delta_grams = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Delta grams"),
    )
    delta_ml = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Delta ml"),
    )
    grams_after = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("Grams after"),
    )
    ml_after = models.FloatField(
        blank=True,
        null=True,
        verbose_name=_("ml after"),
    )
    source_id = models.IntegerField(
        blank=True,
        null=True,
        verbose_name=_("Source ID"),
        help_text=_("Feeding PK that caused this event, if any."),
    )
    note = models.CharField(blank=True, default="", max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()

    class Meta:
        default_permissions = ("view",)
        ordering = ["-created_at"]
        verbose_name = _("Formula Stock Event")
        verbose_name_plural = _("Formula Stock Events")

    def __str__(self):
        target = self.stock_id or self.prepared_feed_id
        return "{} — #{} ({:+g}g / {:+g}ml)".format(
            self.get_type_display(), target, self.delta_grams or 0, self.delta_ml or 0
        )
