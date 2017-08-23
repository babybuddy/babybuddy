# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.views.generic.detail import DetailView

import plotly.offline as plotly
import plotly.graph_objs as go

from core.models import Child, DiaperChange


class DiaperChangeReport(PermissionRequiredMixin, DetailView):
    """All sleep data for a child."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange.html'

    def get_context_data(self, **kwargs):
        context = super(DiaperChangeReport, self).get_context_data(**kwargs)
        child = context['object']

        # TODO: Move this logic to the model? Where should data processing like
        # this happen?
        changes = DiaperChange.objects.filter(child=child)\
            .annotate(date=TruncDate('time'))\
            .values('date')\
            .annotate(count=Count('id'))\
            .order_by('-date')

        trace1 = go.Scatter(
            x=list(changes.values_list('date', flat=True)),
            y=list(changes.values_list('count', flat=True))
        )
        fig = go.Figure({
            "data": [trace1],
            "layout": go.Layout(title='Diaper Changes')
        })
        div = plotly.plot(fig, output_type='div', include_plotlyjs=False)
        html, javascript = div.split('<script')

        context['html'] = html
        context['javascript'] = '<script' + javascript

        return context


class SleepReport(PermissionRequiredMixin, DetailView):
    """All sleep data for a child."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep.html'

    def get_context_data(self, **kwargs):
        context = super(SleepReport, self).get_context_data(**kwargs)
        return context
