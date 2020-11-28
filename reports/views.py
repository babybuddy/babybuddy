# -*- coding: utf-8 -*-
from datetime import date, datetime, time

from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic.detail import DetailView

from babybuddy.mixins import PermissionRequired403Mixin
from core import models

from . import graphs


class DiaperChangeAmounts(PermissionRequired403Mixin, DetailView):
    """
    Graph of diaper "amounts" - measurements of urine output.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange_amounts.html'

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeAmounts, self).get_context_data(**kwargs)
        child = context['object']
        changes = models.DiaperChange.objects.filter(child=child, amount__gt=0)
        if changes and changes.count() > 0:
            context['html'], context['js'] = \
                graphs.diaperchange_amounts(changes)
        return context


class DiaperChangeLifetimesChildReport(PermissionRequired403Mixin, DetailView):
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
            context['html'], context['js'] = \
                graphs.diaperchange_lifetimes(changes)
        return context


class DiaperChangeTypesChildReport(PermissionRequired403Mixin, DetailView):
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
            context['html'], context['js'] = \
                graphs.diaperchange_types(changes)
        return context


class FeedingAmountsChildReport(PermissionRequired403Mixin, DetailView):
    """
    Graph of daily feeding amounts over time.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/feeding_amounts.html'

    def __init__(self):
        super(FeedingAmountsChildReport, self).__init__()
        self.html = ''
        self.js = ''

    def get_context_data(self, **kwargs):
        context = super(FeedingAmountsChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        instances = models.Feeding.objects.filter(child=child)
        if instances:
            context['html'], context['js'] = graphs.feeding_amounts(instances)
        return context


class FeedingDurationChildReport(PermissionRequired403Mixin, DetailView):
    """
    Graph of feeding durations over time.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/feeding_duration.html'

    def __init__(self):
        super(FeedingDurationChildReport, self).__init__()
        self.html = ''
        self.js = ''

    def get_context_data(self, **kwargs):
        context = super(FeedingDurationChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        instances = models.Feeding.objects.filter(child=child)
        if instances:
            context['html'], context['js'] = graphs.feeding_duration(instances)
        return context


class SleepPatternChildReport(PermissionRequired403Mixin, DetailView):
    """
    Graph of sleep pattern comparing sleep to wake times by day.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep_pattern.html'

    def __init__(self):
        super(SleepPatternChildReport, self).__init__()
        self.html = ''
        self.js = ''

    def get_context_data(self, **kwargs):
        context = super(SleepPatternChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        instances = models.Sleep.objects.filter(child=child).order_by('start')
        if instances:
            context['html'], context['js'] = graphs.sleep_pattern(instances)
        return context


class SleepTotalsChildReport(PermissionRequired403Mixin, DetailView):
    """
    Graph of total sleep by day.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep_totals.html'

    def __init__(self):
        super(SleepTotalsChildReport, self).__init__()
        self.html = ''
        self.js = ''

    def get_context_data(self, **kwargs):
        context = super(SleepTotalsChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        instances = models.Sleep.objects.filter(child=child).order_by('start')
        if instances:
            context['html'], context['js'] = graphs.sleep_totals(instances)
        return context


class StatisticsChildReport(PermissionRequired403Mixin, DetailView):
    """
    General statistics.
    TODO: Refactor template to be more appropriate for reports.
    TODO: Move/refactor relevant tests.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'statistics.html'

    def __init__(self):
        super(StatisticsChildReport, self).__init__()
        self.child = None
        self.stats = []

    def get_context_data(self, **kwargs):
        context = super(StatisticsChildReport, self).get_context_data(
            **kwargs)
        self.child = context['object']
        self.add_diaperchange_statistics()
        self.add_feeding_statistics()
        self.add_nap_statistics()
        self.add_sleep_statistics()
        self.add_weight_statistics()
        context['stats'] = self.stats
        return context

    def add_diaperchange_statistics(self):
        instances = models.DiaperChange.objects.filter(child=self.child) \
            .order_by('time')
        changes = {
            'btwn_total': timezone.timedelta(0),
            'btwn_count': instances.count() - 1,
            'btwn_average': 0.0}
        last_instance = None

        for instance in instances:
            if last_instance:
                changes['btwn_total'] += instance.time - last_instance.time
            last_instance = instance

        if changes['btwn_count'] > 0:
            changes['btwn_average'] = changes['btwn_total'] / changes[
                'btwn_count']

        self.stats.append({
            'type': 'duration',
            'stat': changes['btwn_average'],
            'title': _('Diaper change frequency')})

    def add_feeding_statistics(self):
        feedings = [
            {
                'start': timezone.now() - timezone.timedelta(days=3),
                'title': _('Feeding frequency (past 3 days)')
            },
            {
                'start': timezone.now() - timezone.timedelta(weeks=2),
                'title': _('Feeding frequency (past 2 weeks)')
            },
            {
                'start': timezone.make_aware(
                    datetime.combine(date.min, time(0, 0))
                    + timezone.timedelta(days=1)),
                'title': _('Feeding frequency')
            }
        ]
        for timespan in feedings:
            timespan['btwn_total'] = timezone.timedelta(0)
            timespan['btwn_count'] = 0
            timespan['btwn_average'] = 0.0

        instances = models.Feeding.objects.filter(child=self.child).order_by(
            'start')
        last_instance = None

        for instance in instances:
            if last_instance:
                for timespan in feedings:
                    if last_instance.start > timespan['start']:
                        timespan['btwn_total'] += (instance.start
                                                   - last_instance.end)
                        timespan['btwn_count'] += 1
            last_instance = instance

        for timespan in feedings:
            if timespan['btwn_count'] > 0:
                timespan['btwn_average'] = \
                    timespan['btwn_total'] / timespan['btwn_count']

        for item in feedings:
            self.stats.append({
                'type': 'duration',
                'stat': item['btwn_average'],
                'title': item['title']})

    def add_nap_statistics(self):
        instances = models.Sleep.naps.filter(
            child=self.child).order_by('start')
        naps = {
            'total': instances.aggregate(Sum('duration'))['duration__sum'],
            'count': instances.count(),
            'average': 0.0,
            'avg_per_day': 0.0}
        if naps['count'] > 0:
            naps['average'] = naps['total'] / naps['count']

        naps_avg = instances.annotate(date=TruncDate('start')).values('date') \
            .annotate(naps_count=Count('id')).order_by() \
            .aggregate(Avg('naps_count'))
        naps['avg_per_day'] = naps_avg['naps_count__avg']

        self.stats.append({
            'type': 'duration',
            'stat': naps['average'],
            'title': _('Average nap duration')})
        self.stats.append({
            'type': 'float',
            'stat': naps['avg_per_day'],
            'title': _('Average naps per day')})

    def add_sleep_statistics(self):
        instances = models.Sleep.objects.filter(
            child=self.child).order_by('start')
        sleep = {
            'total': instances.aggregate(Sum('duration'))['duration__sum'],
            'count': instances.count(),
            'average': 0.0,
            'btwn_total': timezone.timedelta(0),
            'btwn_count': instances.count() - 1,
            'btwn_average': 0.0}

        last_instance = None
        for instance in instances:
            if last_instance:
                sleep['btwn_total'] += instance.start - last_instance.end
            last_instance = instance

        if sleep['count'] > 0:
            sleep['average'] = sleep['total'] / sleep['count']
        if sleep['btwn_count'] > 0:
            sleep['btwn_average'] = sleep['btwn_total'] / sleep['btwn_count']

        self.stats.append({
            'type': 'duration',
            'stat': sleep['average'],
            'title': _('Average sleep duration')})
        self.stats.append({
            'type': 'duration',
            'stat': sleep['btwn_average'],
            'title': _('Average awake duration')})

    def add_weight_statistics(self):
        weight = {'change_weekly': 0.0}

        instances = models.Weight.objects.filter(
            child=self.child).order_by('-date')
        newest = instances.first()
        oldest = instances.last()

        if newest != oldest:
            weight_change = newest.weight - oldest.weight
            weeks = (newest.date - oldest.date).days / 7
            weight['change_weekly'] = weight_change / weeks

        self.stats.append({
            'type': 'float',
            'stat': weight['change_weekly'],
            'title': _('Weight change per week')})


class WeightWeightChildReport(PermissionRequired403Mixin, DetailView):
    """
    Graph of weight change over time.
    """
    model = models.Child
    permission_required = ('core.view_child',)
    template_name = 'reports/weight_change.html'

    def get_context_data(self, **kwargs):
        context = super(WeightWeightChildReport, self).get_context_data(
            **kwargs)
        child = context['object']
        objects = models.Weight.objects.filter(child=child)
        if objects:
            context['html'], context['js'] = graphs.weight_weight(objects)
        return context
