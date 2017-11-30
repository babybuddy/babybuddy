# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate

import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_parts

from reports import utils


def feeding_duration(instances):
    """
    Create a graph showing average duration of feeding instances over time.

    This function originally used the Avg() function from django.db.models but
    for some reason it was returning None any time the exact count of entries
    was equal to seven.

    :param instances: a QuerySet of Feeding instances.
    :returns: a tuple of the the graph's html and javascript.
    """
    totals = instances.annotate(date=TruncDate('start')) \
        .values('date') \
        .annotate(count=Count('id')) \
        .annotate(sum=Sum('duration')) \
        .order_by('-date')

    averages = []
    for total in totals:
        averages.append(total['sum']/total['count'])

    trace = go.Bar(
        name='Average duration',
        x=list(totals.values_list('date', flat=True)),
        y=[td.seconds/60 for td in averages],
        hoverinfo='text',
        textposition='outside',
        text=[_duration_string_minutes(td) for td in averages]
    )

    layout_args = utils.default_graph_layout_options()
    layout_args['barmode'] = 'stack'
    layout_args['title'] = '<b>Average Feeding Durations</b>'
    layout_args['xaxis']['title'] = 'Date'
    layout_args['xaxis']['rangeselector'] = utils.rangeselector_date()
    layout_args['yaxis']['title'] = 'Average duration (minutes)'

    fig = go.Figure({
        'data': [trace],
        'layout': go.Layout(**layout_args)
    })
    output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
    return utils.split_graph_output(output)


def _duration_string_minutes(duration):
    """
    Format a "short" duration string with only minutes precision. This is
    intended to fit better in smaller spaces on a graph.
    :returns: a string of the form Xm.
    """
    h, m, s = duration_parts(duration)
    return '{}m'.format(m)
