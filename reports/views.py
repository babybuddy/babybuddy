# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.detail import DetailView

from core.models import Child

from .graphs import diaperchange_types, sleep_times


class DiaperChangesChildReport(PermissionRequiredMixin, DetailView):
    """Diaper change information by type."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange.html'

    def get_context_data(self, **kwargs):
        context = super(DiaperChangesChildReport, self).get_context_data(**kwargs)
        child = context['object']
        context['html'], context['javascript'] = diaperchange_types(child)
        return context


class SleepChildReport(PermissionRequiredMixin, DetailView):
    """All sleep times by date."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep.html'

    def __init__(self):
        super(SleepChildReport, self).__init__()
        self.html = ''
        self.javascript = ''

    def get_context_data(self, **kwargs):
        context = super(SleepChildReport, self).get_context_data(**kwargs)
        child = context['object']
        context['html'], context['javascript'] = sleep_times(child)
        return context
