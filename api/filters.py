# -*- coding: utf-8 -*-
from django_filters import rest_framework as filters
from core import models


class TimeFieldFilter(filters.FilterSet):
    date = filters.DateFilter(field_name='time__date', label='Date')
    date_min = filters.DateFilter(field_name='time__date', label='Min. Date',
                                  lookup_expr='gte')
    date_max = filters.DateFilter(field_name='time__date', label='Max. Date',
                                  lookup_expr='lte')


class StartEndFieldFilter(filters.FilterSet):
    end = filters.DateFilter(field_name='end__date', label='End Date')
    end_min = filters.DateFilter(field_name='end__date', label='Min. End Date',
                                 lookup_expr='gte')
    end_max = filters.DateFilter(field_name='end__date', label='Max. End Date',
                                 lookup_expr='lte')
    start = filters.DateFilter(field_name='start__date', label='Start Date')
    start_min = filters.DateFilter(field_name='start__date', lookup_expr='gte',
                                   label='Min. Start Date',)
    start_end = filters.DateFilter(field_name='start__date', lookup_expr='lte',
                                   label='Max. End Date')


class DiaperChangeFilter(TimeFieldFilter):
    class Meta:
        model = models.DiaperChange
        fields = ['child', 'wet', 'solid', 'color', 'amount']


class FeedingFilter(StartEndFieldFilter):
    class Meta:
        model = models.Feeding
        fields = ['child', 'type', 'method']


class NoteFilter(TimeFieldFilter):
    class Meta:
        model = models.Note
        fields = ['child']


class SleepFilter(StartEndFieldFilter):
    class Meta:
        model = models.Sleep
        fields = ['child']


class TemperatureFilter(TimeFieldFilter):
    class Meta:
        model = models.Temperature
        fields = ['child']


class TimerFilter(StartEndFieldFilter):
    class Meta:
        model = models.Timer
        fields = ['child', 'active', 'user']


class TummyTimeFilter(StartEndFieldFilter):
    class Meta:
        model = models.TummyTime
        fields = ['child']
