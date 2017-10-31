# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.detail import DetailView
from django.utils import timezone

from core.models import Child, DiaperChange, Sleep

from .graphs import (diaperchange_types, diaperchange_lifetimes, sleep_pattern,
                     sleep_totals, timeline)


class DiaperChangeLifetimesChildReport(PermissionRequiredMixin, DetailView):
    """Graph of diaper changes by day and type.
    """
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange_lifetimes.html'

    def get_context_data(self, **kwargs):
        context = super(
            DiaperChangeLifetimesChildReport, self).get_context_data(**kwargs)
        child = context['object']
        changes = DiaperChange.objects.filter(child=child)
        if changes and changes.count() > 1:
            context['html'], context['javascript'] = diaperchange_lifetimes(
                changes)
        return context


class DiaperChangeTypesChildReport(PermissionRequiredMixin, DetailView):
    """Graph of diaper changes by day and type.
    """
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange_types.html'

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeTypesChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        changes = DiaperChange.objects.filter(child=child)
        if changes:
            context['html'], context['javascript'] = diaperchange_types(
                changes)
        return context


class SleepPatternChildReport(PermissionRequiredMixin, DetailView):
    """Graph of sleep pattern comparing sleep to wake times by day.
    """
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep_pattern.html'

    def __init__(self):
        super(SleepPatternChildReport, self).__init__()
        self.html = ''
        self.javascript = ''

    def get_context_data(self, **kwargs):
        context = super(SleepPatternChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        instances = Sleep.objects.filter(child=child).order_by('start')
        if instances:
            context['html'], context['javascript'] = sleep_pattern(instances)
        return context


class SleepTotalsChildReport(PermissionRequiredMixin, DetailView):
    """Graph of total sleep by day.
    """
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep_totals.html'

    def __init__(self):
        super(SleepTotalsChildReport, self).__init__()
        self.html = ''
        self.javascript = ''

    def get_context_data(self, **kwargs):
        context = super(SleepTotalsChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        instances = Sleep.objects.filter(child=child).order_by('start')
        if instances:
            context['html'], context['javascript'] = sleep_totals(instances)
        return context


class TimelineChildReport(PermissionRequiredMixin, DetailView):
    """Chronological daily view of events (non-graph).
    """
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/timeline.html'

    def get_context_data(self, **kwargs):
        context = super(TimelineChildReport, self).get_context_data(**kwargs)
        date = self.request.GET.get('date', str(timezone.localdate()))
        date = timezone.datetime.strptime(date, '%Y-%m-%d')
        date = timezone.localtime(timezone.make_aware(date))
        context['objects'] = timeline(self.object, date)
        context['date'] = date
        context['date_previous'] = date - timezone.timedelta(days=1)
        context['date_next'] = date + timezone.timedelta(days=1)
        return context
