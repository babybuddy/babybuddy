# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.utils import timezone
from django.views.generic.detail import DetailView

from core.models import Child, Sleep


class SleepReport(PermissionRequiredMixin, DetailView):
    """All sleep data for a child."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep.html'

    def get_context_data(self, **kwargs):
        context = super(SleepReport, self).get_context_data(**kwargs)
        child = context['object']

        sleep_entries = Sleep.objects.filter(child=child).order_by('-end')
        diff = timezone.localtime().date() - timezone.localtime(sleep_entries.last().end).date()
        stats = OrderedDict()
        for x in range(0, diff.days + 1):
            key = (timezone.localtime() - timezone.timedelta(days=x))
            stats[key.date()] = []

        last = None
        for entry in sleep_entries:
            start = timezone.localtime(entry.start)
            end = timezone.localtime(entry.end)

            if not stats[end.date()]:
                last = end.replace(hour=23, minute=59, second=59)

            # TODO: Account for sleep sessions crossing midnight.
            stats[start.date()].append((
                (last - end).seconds/86400 * 100,
                (end - start).seconds/86400 * 100
            ))
            last = start

        context['stats'] = stats

        return context
