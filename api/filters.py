# -*- coding: utf-8 -*-
from core import models
from django_filters import rest_framework as filters


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass


class ChildFieldFilter(filters.FilterSet):
    class Meta:
        abstract = True
        fields = ["child"]


class TagsFieldFilter(filters.FilterSet):
    tags = CharInFilter(
        field_name="tags__name",
        label="tag",
        help_text="A list of tag names, comma separated",
    )

    class Meta:
        abstract = True


class TimeFieldFilter(ChildFieldFilter):
    date = filters.IsoDateTimeFilter(field_name="time", label="DateTime")
    date_max = filters.IsoDateTimeFilter(
        field_name="time", label="Max. DateTime", lookup_expr="lte"
    )
    date_min = filters.IsoDateTimeFilter(
        field_name="time", label="Min. DateTime", lookup_expr="gte"
    )

    class Meta:
        abstract = True
        fields = sorted(ChildFieldFilter.Meta.fields + ["date", "date_max", "date_min"])


class StartEndFieldFilter(ChildFieldFilter):
    end = filters.IsoDateTimeFilter(field_name="end", label="End DateTime")
    end_max = filters.IsoDateTimeFilter(
        field_name="end", label="Max. End DateTime", lookup_expr="lte"
    )
    end_min = filters.IsoDateTimeFilter(
        field_name="end", label="Min. End DateTime", lookup_expr="gte"
    )
    start = filters.IsoDateTimeFilter(field_name="start", label="Start DateTime")
    start_max = filters.IsoDateTimeFilter(
        field_name="start", lookup_expr="lte", label="Max. End DateTime"
    )
    start_min = filters.IsoDateTimeFilter(
        field_name="start", lookup_expr="gte", label="Min. Start DateTime"
    )

    class Meta:
        abstract = True
        fields = sorted(
            ChildFieldFilter.Meta.fields
            + ["end", "end_max", "end_min", "start", "start_max", "start_min"]
        )


class DiaperChangeFilter(TimeFieldFilter, TagsFieldFilter):
    class Meta(TimeFieldFilter.Meta):
        model = models.DiaperChange
        fields = sorted(
            TimeFieldFilter.Meta.fields + ["wet", "solid", "color", "amount"]
        )


class FeedingFilter(StartEndFieldFilter, TagsFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.Feeding
        fields = sorted(StartEndFieldFilter.Meta.fields + ["type", "method"])


class FoodFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = models.Food
        fields = ["name", "category", "allergen", "active"]


class MealFilter(TimeFieldFilter, TagsFieldFilter):
    food = filters.ModelChoiceFilter(
        field_name="foods",
        queryset=models.Food.objects.all(),
        distinct=True,
    )
    category = filters.ChoiceFilter(
        field_name="foods__category",
        choices=models.Food._meta.get_field("category").choices,
        distinct=True,
    )

    class Meta(TimeFieldFilter.Meta):
        model = models.Meal
        fields = sorted(
            TimeFieldFilter.Meta.fields
            + ["meal_type", "quantity", "preparation", "food", "category"]
        )


class ChildFoodProfileFilter(ChildFieldFilter):
    category = filters.ChoiceFilter(
        field_name="food__category",
        choices=models.Food._meta.get_field("category").choices,
    )

    class Meta(ChildFieldFilter.Meta):
        model = models.ChildFoodProfile
        fields = sorted(
            ChildFieldFilter.Meta.fields
            + ["food", "category", "taste", "tolerance"]
        )


class MedicationFilter(TimeFieldFilter, TagsFieldFilter):
    class Meta(TimeFieldFilter.Meta):
        model = models.Medication
        fields = sorted(TimeFieldFilter.Meta.fields + ["name", "dosage_unit"])


class NoteFilter(TimeFieldFilter, TagsFieldFilter):
    class Meta(TimeFieldFilter.Meta):
        model = models.Note


class PumpingFilter(StartEndFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.Pumping


class SleepFilter(StartEndFieldFilter, TagsFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.Sleep


class TemperatureFilter(TimeFieldFilter, TagsFieldFilter):
    class Meta(TimeFieldFilter.Meta):
        model = models.Temperature


class TimerFilter(StartEndFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.Timer
        fields = sorted(StartEndFieldFilter.Meta.fields + ["name", "user"])


class TummyTimeFilter(StartEndFieldFilter, TagsFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.TummyTime
