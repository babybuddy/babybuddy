# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.detail import DetailView

from core import models

from . import graphs


class DiaperChangeLifetimesChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of diaper "lifetimes" - time between diaper changes.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange_lifetimes.html'

    def get_context_data(self, **kwargs):
        context = super(
            DiaperChangeLifetimesChildReport, self).get_context_data(**kwargs)
        child = context['object']
        changes = models.DiaperChange.objects.filter(child=child)
        if changes and changes.count() > 1:
            context['html'], context['javascript'] = \
                graphs.diaperchange_lifetimes(changes)
        return context


class DiaperChangeTypesChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of diaper changes by day and type.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange_types.html'

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeTypesChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        changes = models.DiaperChange.objects.filter(child=child)
        if changes:
            context['html'], context['javascript'] = \
                graphs.diaperchange_types(changes)
        return context


class FeedingDurationChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of feeding durations over time.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/feeding_duration.html'

    def __init__(self):
        super(FeedingDurationChildReport, self).__init__()
        self.html = ''
        self.javascript = ''

    def get_context_data(self, **kwargs):
        context = super(FeedingDurationChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        instances = models.Feeding.objects.filter(child=child)
        if instances:
            context['html'], context['javascript'] = \
                graphs.feeding_duration(instances)
        return context


class SleepPatternChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of sleep pattern comparing sleep to wake times by day.
    """
    model = models.Child
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
        instances = models.Sleep.objects.filter(child=child).order_by('start')
        if instances:
            context['html'], context['javascript'] = \
                graphs.sleep_pattern(instances)
        return context


class SleepTotalsChildReport(PermissionRequiredMixin, DetailView):
    """
    Graph of total sleep by day.
    """
    model = models.Child
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
        instances = models.Sleep.objects.filter(child=child).order_by('start')
        if instances:
            context['html'], context['javascript'] = \
                graphs.sleep_totals(instances)
        return context


class WeightWeightChildReoport(PermissionRequiredMixin, DetailView):
    """
    Graph of weight change over time.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/weight_change.html'

    def get_context_data(self, **kwargs):
        context = super(WeightWeightChildReoport, self).get_context_data(
            **kwargs)
        child = context['object']
        objects = models.Weight.objects.filter(child=child)
        if objects:
            context['html'], context['javascript'] = \
                graphs.weight_weight(objects)
        return context
