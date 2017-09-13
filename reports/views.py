# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.detail import DetailView

from core.models import Child

from .graphs import diaperchange_types, sleep_pattern, sleep_totals


class DiaperChangeTypesChildReport(PermissionRequiredMixin, DetailView):
    """Graph of diaper changes by day and type."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange_types.html'

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeTypesChildReport, self).get_context_data(**kwargs)
        child = context['object']
        context['html'], context['javascript'] = diaperchange_types(child)
        return context


class SleepPatternChildReport(PermissionRequiredMixin, DetailView):
    """Graph of sleep pattern comparing sleep to wake times by day."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep_pattern.html'

    def __init__(self):
        super(SleepPatternChildReport, self).__init__()
        self.html = ''
        self.javascript = ''

    def get_context_data(self, **kwargs):
        context = super(SleepPatternChildReport, self).get_context_data(**kwargs)
        child = context['object']
        context['html'], context['javascript'] = sleep_pattern(child)
        return context


class SleepTotalsChildReport(PermissionRequiredMixin, DetailView):
    """Graph of total sleep by day."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep_totals.html'

    def __init__(self):
        super(SleepTotalsChildReport, self).__init__()
        self.html = ''
        self.javascript = ''

    def get_context_data(self, **kwargs):
        context = super(SleepTotalsChildReport, self).get_context_data(**kwargs)
        child = context['object']
        context['html'], context['javascript'] = sleep_totals(child)
        return context
