# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count, Case, When
from django.db.models.functions import TruncDate
from django.views.generic.detail import DetailView

import plotly.offline as plotly
import plotly.graph_objs as go

from core.models import Child, DiaperChange

from .utils import default_graph_layout_options, split_graph_output


class DiaperChangesChildReport(PermissionRequiredMixin, DetailView):
    """All sleep data for a child."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/diaperchange.html'

    def __init__(self):
        super(DiaperChangesChildReport, self).__init__()
        self.html = ''
        self.javascript = ''

    def get_context_data(self, **kwargs):
        context = super(DiaperChangesChildReport, self).get_context_data(**kwargs)
        child = context['object']
        self._change_types_over_time(child)
        context['html'] = self.html
        context['javascript'] = self.javascript
        return context

    def _change_types_over_time(self, child):
        changes = DiaperChange.objects.filter(child=child) \
            .annotate(date=TruncDate('time')) \
            .values('date') \
            .annotate(wet_count=Count(Case(When(wet=True, then=1)))) \
            .annotate(solid_count=Count(Case(When(solid=True, then=1)))) \
            .annotate(total=Count('id')) \
            .order_by('-date')

        solid_trace = go.Scatter(
            mode='markers',
            name='Solid changes',
            x=list(changes.values_list('date', flat=True)),
            y=list(changes.values_list('solid_count', flat=True)),
        )
        wet_trace = go.Scatter(
            mode='markers',
            name='Wet changes',
            x=list(changes.values_list('date', flat=True)),
            y=list(changes.values_list('wet_count', flat=True))
        )
        total_trace = go.Scatter(
            name='Total changes',
            x=list(changes.values_list('date', flat=True)),
            y=list(changes.values_list('total', flat=True))
        )

        layout_args = default_graph_layout_options()
        layout_args['barmode'] = 'stack'
        layout_args['title'] = 'Diaper change types over time'
        layout_args['xaxis']['title'] = 'Date'
        layout_args['yaxis']['title'] = 'Number of changes'

        fig = go.Figure({
            'data': [solid_trace, wet_trace, total_trace],
            'layout': go.Layout(**layout_args)
        })
        output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
        html, javascript = split_graph_output(output)
        self.html += '<a name="change_types_over_time">' + html
        self.javascript += javascript


class SleepChildReport(PermissionRequiredMixin, DetailView):
    """All sleep data for a child."""
    model = Child
    permission_required = ('core.view_child',)
    template_name = 'reports/sleep.html'
