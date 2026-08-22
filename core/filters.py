# -*- coding: utf-8 -*-
from django.utils.translation import gettext as _

import django_filters

from core import models


class TagFilter(django_filters.FilterSet):
    tag = django_filters.ModelChoiceFilter(
        label=_("Tag"),
        field_name="tags__name",
        distinct=True,
        queryset=models.Tag.objects.all().order_by("name"),
    )


class BMIFilter(TagFilter):
    class Meta:
        model = models.BMI
        fields = ["child"]


class DiaperChangeFilter(TagFilter):
    class Meta:
        model = models.DiaperChange
        fields = ["child", "wet", "solid", "color"]


class FeedingFilter(TagFilter):
    class Meta:
        model = models.Feeding
        fields = ["child", "type", "method"]


class HeadCircumferenceFilter(TagFilter):
    class Meta:
        model = models.HeadCircumference
        fields = ["child"]


class HeightFilter(TagFilter):
    class Meta:
        model = models.Height
        fields = ["child"]


class MedicationFilter(TagFilter):
    class Meta:
        model = models.Medication
        fields = ["child", "name", "dosage_unit"]


class NoteFilter(TagFilter):
    class Meta:
        model = models.Note
        fields = ["child"]


class PumpingFilter(TagFilter):
    class Meta:
        model = models.Pumping
        fields = ["child"]


class SleepFilter(TagFilter):
    class Meta:
        model = models.Sleep
        fields = ["child"]


class TagFilter(django_filters.FilterSet):
    class Meta:
        model = models.Tag
        fields = {"name": ["contains"]}


class TemperatureFilter(TagFilter):
    class Meta:
        model = models.Temperature
        fields = ["child"]


class TummyTimeFilter(TagFilter):
    class Meta:
        model = models.TummyTime
        fields = ["child"]


class WeightFilter(TagFilter):
    class Meta:
        model = models.Weight
        fields = ["child"]


class SupplyItemFilter(django_filters.FilterSet):
    class Meta:
        model = models.SupplyItem
        fields = ["product_line__item_type", "product_line__brand", "size"]


class FeedInventoryFilter(TagFilter):
    class Meta:
        model = models.FeedInventory
        fields = ["child", "storage_location", "status"]


class FormulaStockFilter(django_filters.FilterSet):
    class Meta:
        model = models.FormulaStock
        fields = ["product_line__brand", "form", "is_reserve"]


class PreparedFeedFilter(django_filters.FilterSet):
    class Meta:
        model = models.PreparedFeed
        fields = ["prepared_from", "status"]

