# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from django.db.models import Count, Case, When
from django.db.models.functions import TruncDate
from django.utils import timezone

import pandas as pd
import plotly.offline as plotly
import plotly.graph_objs as go

from core.models import DiaperChange, Sleep
from core.utils import duration_string

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
    """Create a graph showing blocked out periods of sleep during each day."""
    instances = Sleep.objects.filter(child=child).order_by('start')
    y_df = pd.DataFrame()
    text_df = pd.DataFrame()
    last_end_time = None
    adjustment = None
    df_index = 0
    for instance in instances:
        start_time = timezone.localtime(instance.start)
        end_time = timezone.localtime(instance.end)
        start_date = start_time.date().isoformat()
        duration = instance.duration

        # Check if the previous entry crossed midnight (see below).
        if adjustment:
            # Fake (0) entry to keep the color switching logic working.
            df_index = _add_sleep_entry(
                y_df, text_df, 0, adjustment['column'], 0)
            # Real adjustment entry.
            df_index = _add_sleep_entry(
                y_df,
                text_df,
                df_index,
                adjustment['column'],
                adjustment['duration'].seconds/60,
                'Asleep {} ({} to {})'.format(
                    duration_string(adjustment['duration']),
                    adjustment['start_time'].strftime('%I:%M %p'),
                    adjustment['end_time'].strftime('%I:%M %p')
                )
            )
            last_end_time = timezone.localtime(adjustment['end_time'])
            adjustment = None

        # If the dates do not match, set up an adjustment for the next day.
        if end_time.date() != start_time.date():
            adj_start_time = end_time.replace(hour=0, minute=0, second=0)
            adjustment = {
                'column': end_time.date().isoformat(),
                'start_time': adj_start_time,
                'end_time': end_time,
                'duration': end_time - adj_start_time
            }

            # Adjust end_time for the current entry.
            end_time = end_time.replace(
                day=start_time.day, hour=23, minute=59, second=0)
            duration = end_time - start_time

        if start_date not in y_df:
            last_end_time = start_time.replace(hour=0, minute=0, second=0)

        # Awake time.
        df_index = _add_sleep_entry(
            y_df,
            text_df,
            df_index,
            start_date,
            (start_time - last_end_time).seconds/60
        )

        # Asleep time.
        df_index = _add_sleep_entry(
            y_df,
            text_df,
            df_index,
            start_date,
            duration.seconds/60,
            'Asleep {} ({} to {})'.format(
                duration_string(duration),
                start_time.strftime('%I:%M %p'),
                end_time.strftime('%I:%M %p')
            )
        )

        last_end_time = end_time

    dates = list(y_df)
    traces = []
    color = 'rgba(255, 255, 255, 0)'
    for index, row in y_df.iterrows():
        traces.append(go.Bar(
            x=dates,
            y=row,
            text=text_df.ix[index],
            hoverinfo='text',
            marker={'color': color},
            showlegend=False,
        ))
        if color == 'rgba(255, 255, 255, 0)':
            color = 'rgb(0, 0, 255)'
        else:
            color = 'rgba(255, 255, 255, 0)'

    layout_args = default_graph_layout_options()
    layout_args['margin']['b'] = 100

    layout_args['barmode'] = 'stack'
    layout_args['hovermode'] = 'closest'
    layout_args['title'] = 'Sleep vs. wake times'
    layout_args['height'] = 600

    layout_args['xaxis']['title'] = 'Date'
    layout_args['xaxis']['type'] = 'category'
    layout_args['xaxis']['tickangle'] = -65

    start = timezone.localtime().strptime('12:00 AM', '%I:%M %p')
    ticks = OrderedDict()
    ticks[0] = start.strftime('%I:%M %p')
    for i in range(30, 60*24, 30):
        ticks[i] = (start + timezone.timedelta(minutes=i)).strftime('%I:%M %p')

    layout_args['yaxis']['title'] = 'Time of day'
    layout_args['yaxis']['rangemode'] = 'tozero'
    layout_args['yaxis']['tickmode'] = 'array'
    layout_args['yaxis']['tickvals'] = list(ticks.keys())
    layout_args['yaxis']['ticktext'] = list(ticks.values())
    layout_args['yaxis']['tickfont'] = {'size': 10}

    fig = go.Figure({
        'data': traces,
        'layout': go.Layout(**layout_args)
    })
    output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
    return split_graph_output(output)


def _add_sleep_entry(y_df, text_df, index, column, duration, text=''):
    """Create a duration and text description entry in a DataFrame and return
    the next index on success."""
    if column not in y_df:
        y_df.assign(**{column: 0 in range(0, len(y_df.index))})
        text_df.assign(**{column: 0 in range(0, len(text_df.index))})
        index = 0

    y_df.set_value(index, column, duration)
    text_df.set_value(index, column, text)
    return index + 1
