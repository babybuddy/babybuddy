# -*- coding: utf-8 -*-
import warnings

from core import models
from django_filters import rest_framework as filters


class DjangoFilterBackend(filters.DjangoFilterBackend):
    """
    django-filter 25.0 removed `get_schema_operation_parameters` in favor of
    drf-spectacular, but Baby Buddy still publishes an OpenAPI schema built by
    Django REST Framework's `generateschema` command, which requires it. This
    restores the implementation django-filter used to provide so that filter
    fields continue to appear in "openapi-schema.yml".
    """

    def get_schema_operation_parameters(self, view):
        try:
            queryset = view.get_queryset()
        except Exception:
            queryset = None
            warnings.warn(
                "{} is not compatible with schema generation".format(view.__class__),
                stacklevel=2,
            )

        filterset_class = self.get_filterset_class(view, queryset)
        if not filterset_class:
            return []

        parameters = []
        for field_name, field in filterset_class.base_filters.items():
            parameter = {
                "name": field_name,
                "required": field.extra["required"],
                "in": "query",
                "description": field.label if field.label is not None else field_name,
                "schema": {"type": "string"},
            }
            if field.extra and "choices" in field.extra:
                parameter["schema"]["enum"] = [c[0] for c in field.extra["choices"]]
            parameters.append(parameter)
        return parameters


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


class ActivityFilter(StartEndFieldFilter, TagsFieldFilter):
    class Meta(StartEndFieldFilter.Meta):
        model = models.Activity
        fields = sorted(StartEndFieldFilter.Meta.fields + ["type"])


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
