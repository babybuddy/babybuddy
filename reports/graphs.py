# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import Count, Case, When
from django.db.models.functions import TruncDate
from django.utils import timezone

import pandas as pd
import plotly.offline as plotly
import plotly.graph_objs as go

from core.models import DiaperChange, Sleep

from .utils import default_graph_layout_options, split_graph_output


def diaperchange_types(child):
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
    layout_args['title'] = 'Diaper Change types'
    layout_args['xaxis']['title'] = 'Date'
    layout_args['yaxis']['title'] = 'Number of changes'

    fig = go.Figure({
        'data': [solid_trace, wet_trace, total_trace],
        'layout': go.Layout(**layout_args)
    })
    output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
    return split_graph_output(output)


def sleep_times(child):
    instances = Sleep.objects.filter(child=child).order_by('start')
    df = pd.DataFrame()
    last_end_time = None
    df_index = 0
    for instance in instances:
        start_time = timezone.localtime(instance.start)
        end_time = timezone.localtime(instance.end)
        start_date = start_time.date().isoformat()
        if start_date not in df:
            df.assign(**{start_date: 0 in range(0, len(df.index))})
            last_end_time = start_time.replace(hour=0, minute=0, second=0)
            df_index = 0
        df.set_value(
            df_index, start_date, (start_time - last_end_time).seconds/60)
        df_index += 1
        df.set_value(df_index, start_date, instance.duration.seconds/60)
        df_index += 1
        last_end_time = end_time

    dates = list(df)
    traces = []
    color = 'rgba(255, 255, 255, 0)'
    for index, row in df.iterrows():
        traces.append(go.Bar(
            x=dates,
            y=row,
            marker={'color': color},
            showlegend=False,
        ))
        if color == 'rgba(255, 255, 255, 0)':
            color = 'rgb(0, 0, 255)'
        else:
            color = 'rgba(255, 255, 255, 0)'

    layout_args = default_graph_layout_options()

    layout_args['barmode'] = 'stack'
    layout_args['hovermode'] = 'closest'
    layout_args['title'] = 'Sleep entries per day'

    layout_args['xaxis']['title'] = 'Date'
    layout_args['xaxis']['type'] = 'category'

    layout_args['yaxis']['title'] = 'Time of day'
    layout_args['yaxis']['rangemode'] = 'tozero'
    layout_args['yaxis']['tickmode'] = 'array'
    layout_args['yaxis']['tickvals'] = list(range(0, 1441, 60))
    layout_args['yaxis']['ticktext'] = list(range(0, 1441, 60))

    fig = go.Figure({
        'data': traces,
        'layout': go.Layout(**layout_args)
    })
    output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
    return split_graph_output(output)
