# -*- coding: utf-8 -*-
from django_filters import rest_framework as filters
from core import models


class ChildFieldFilter(filters.FilterSet):
    class Meta:
        abstract = True
        fields = ["child"]


class TimeFieldFilter(ChildFieldFilter):
    date = filters.DateFilter(field_name="time__date", label="Date")
    date_max = filters.DateFilter(
        field_name="time__date", label="Max. Date", lookup_expr="lte"
    )
    date_min = filters.DateFilter(
        field_name="time__date", label="Min. Date", lookup_expr="gte"
    )

    class Meta:
        abstract = True
        fields = sorted(ChildFieldFilter.Meta.fields + ["date", "date_max", "date_min"])


class StartEndFieldFilter(ChildFieldFilter):
    end = filters.DateFilter(field_name="end__date", label="End Date")
    end_max = filters.DateFilter(
        field_name="end__date", label="Max. End Date", lookup_expr="lte"
    )
    end_min = filters.DateFilter(
        field_name="end__date", label="Min. End Date", lookup_expr="gte"
    )
    start = filters.DateFilter(field_name="start__date", label="Start Date")
    start_max = filters.DateFilter(
        field_name="start__date", lookup_expr="lte", label="Max. End Date"
    )
    start_min = filters.DateFilter(
        field_name="start__date", lookup_expr="gte", label="Min. Start Date"
    )

    class Meta:
        abstract = True
        fields = sorted(
            ChildFieldFilter.Meta.fields
            + ["end", "end_max", "end_min", "start", "start_max", "start_min"]
        )


class DiaperChangeFilter(TimeFieldFilter):
    class Meta(TimeFieldFilter.Meta):
        model = models.DiaperChange
        fields = sorted(
            TimeFieldFilter.Meta.fields + ["wet", "solid", "color", "amount"]
        )


class FeedingFilter(StartEndFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.Feeding
        fields = sorted(StartEndFieldFilter.Meta.fields + ["type", "method"])


class NoteFilter(TimeFieldFilter):
    class Meta(TimeFieldFilter.Meta):
        model = models.Note


class SleepFilter(StartEndFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.Sleep


class TemperatureFilter(TimeFieldFilter):
    class Meta(TimeFieldFilter.Meta):
        model = models.Temperature


class TimerFilter(StartEndFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.Timer
        fields = sorted(StartEndFieldFilter.Meta.fields + ["active", "user"])


class TummyTimeFilter(StartEndFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.TummyTime
