# -*- coding: utf-8 -*-
from django_filters import rest_framework as filters
from core import models


class DateFromTimeFieldFilter(filters.FilterSet):
    date = filters.DateFilter(field_name='date', label='Date')
    date_min = filters.DateFilter(field_name='time__date', label='Min. Date',
                                  lookup_expr='gte')
    date_max = filters.DateFilter(field_name='time__date', label='Max. Date',
                                  lookup_expr='lte')


class DiaperChangeFilter(DateFromTimeFieldFilter):
    class Meta:
        model = models.DiaperChange
        fields = ['child', 'wet', 'solid', 'color', 'amount']


class NoteFilter(DateFromTimeFieldFilter):
    class Meta:
        model = models.Note
        fields = ['child']


class TemperatureFilter(DateFromTimeFieldFilter):
    class Meta:
        model = models.Temperature
        fields = ['child']
