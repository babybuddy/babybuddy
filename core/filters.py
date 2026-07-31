# -*- coding: utf-8 -*-
from django.utils.translation import gettext as _

import django_filters

from babybuddy.widgets import DateInput
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


class FoodFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        field_name="name",
        lookup_expr="icontains",
        label=_("Name"),
    )

    class Meta:
        model = models.Food
        fields = ["name", "category", "allergen", "active"]


class MealFilter(TagFilter):
    date_from = django_filters.DateFilter(
        field_name="time",
        lookup_expr="date__gte",
        label=_("From date"),
        widget=DateInput(),
    )
    date_to = django_filters.DateFilter(
        field_name="time",
        lookup_expr="date__lte",
        label=_("To date"),
        widget=DateInput(),
    )
    food = django_filters.ModelChoiceFilter(
        field_name="foods",
        distinct=True,
        label=_("Food"),
        queryset=models.Food.objects.all(),
    )
    category = django_filters.ChoiceFilter(
        field_name="foods__category",
        distinct=True,
        label=_("Category"),
        choices=models.Food._meta.get_field("category").choices,
    )

    class Meta:
        model = models.Meal
        fields = ["child", "meal_type", "quantity"]


class ChildFoodProfileFilter(django_filters.FilterSet):
    food = django_filters.ModelChoiceFilter(
        queryset=models.Food.objects.all(),
        label=_("Food"),
    )
    category = django_filters.ChoiceFilter(
        field_name="food__category",
        label=_("Category"),
        choices=models.Food._meta.get_field("category").choices,
    )

    class Meta:
        model = models.ChildFoodProfile
        fields = ["child", "food", "category", "taste", "tolerance"]


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
