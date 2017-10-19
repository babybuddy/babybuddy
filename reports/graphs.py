# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

from django.db.models import Count, Case, When
from django.db.models.functions import TruncDate
from django.utils import timezone

import pandas as pd
import plotly.offline as plotly
import plotly.graph_objs as go

from core.models import DiaperChange, Feeding, Sleep, TummyTime
from core.utils import duration_string, duration_parts

from . import utils


def diaperchange_lifetimes(child):
    """Create a graph showing how long diapers last (time between changes)."""
    changes = DiaperChange.objects.filter(child=child).order_by('time')

    durations = []
    last_change = changes.first()
    for change in changes[1:]:
        duration = change.time - last_change.time
        if duration.seconds > 0:
            durations.append(duration)
        last_change = change

    trace = go.Box(
        y=[round(d.seconds/3600, 2) for d in durations],
        name='Changes',
        jitter=0.3,
        pointpos=-1.8,
        boxpoints='all'
    )

    layout_args = utils.default_graph_layout_options()
    layout_args['height'] = 800
    layout_args['title'] = '<b>Diaper Lifetimes</b><br>{}'.format(child)
    layout_args['yaxis']['title'] = 'Time between changes (hours)'
    layout_args['yaxis']['zeroline'] = False
    layout_args['yaxis']['dtick'] = 1

    fig = go.Figure({
        'data': [trace],
        'layout': go.Layout(**layout_args)
    })
    output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
    return utils.split_graph_output(output)


def diaperchange_types(child):
    """Create a graph showing types of totals for diaper changes."""
    changes = DiaperChange.objects.filter(child=child) \
        .annotate(date=TruncDate('time')) \
        .values('date') \
        .annotate(wet_count=Count(Case(When(wet=True, then=1)))) \
        .annotate(solid_count=Count(Case(When(solid=True, then=1)))) \
        .annotate(total=Count('id')) \
        .order_by('-date')

    solid_trace = go.Scatter(
        mode='markers',
        name='Solid',
        x=list(changes.values_list('date', flat=True)),
        y=list(changes.values_list('solid_count', flat=True)),
    )
    wet_trace = go.Scatter(
        mode='markers',
        name='Wet',
        x=list(changes.values_list('date', flat=True)),
        y=list(changes.values_list('wet_count', flat=True))
    )
    total_trace = go.Scatter(
        name='Total',
        x=list(changes.values_list('date', flat=True)),
        y=list(changes.values_list('total', flat=True))
    )

    layout_args = utils.default_graph_layout_options()
    layout_args['barmode'] = 'stack'
    layout_args['title'] = '<b>Diaper Change Types</b><br>{}'.format(child)
    layout_args['xaxis']['title'] = 'Date'
    layout_args['xaxis']['rangeselector'] = utils.rangeselector_date()
    layout_args['yaxis']['title'] = 'Number of changes'

    fig = go.Figure({
        'data': [solid_trace, wet_trace, total_trace],
        'layout': go.Layout(**layout_args)
    })
    output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
    return utils.split_graph_output(output)


def sleep_totals(child):
    """Create a graph showing total time sleeping for each day."""
    instances = Sleep.objects.filter(child=child).order_by('start')

    totals = {}
    for instance in instances:
        start = timezone.localtime(instance.start)
        end = timezone.localtime(instance.end)
        if start.date() not in totals.keys():
            totals[start.date()] = timezone.timedelta(seconds=0)
        if end.date() not in totals.keys():
            totals[end.date()] = timezone.timedelta(seconds=0)

        # Account for dates crossing midnight.
        if start.date() != end.date():
            totals[start.date()] += end.replace(
                year=start.year, month=start.month, day=start.day,
                hour=23, minute=59, second=59) - start
            totals[end.date()] += end - start.replace(
                year=end.year, month=end.month, day=end.day, hour=0, minute=0,
                second=0)
        else:
            totals[start.date()] += instance.duration

    trace = go.Bar(
        name='Total sleep',
        x=list(totals.keys()),
        y=[td.seconds/3600 for td in totals.values()],
        hoverinfo='text',
        textposition='outside',
        text=[_duration_string_short(td) for td in totals.values()]
    )

    layout_args = utils.default_graph_layout_options()
    layout_args['barmode'] = 'stack'
    layout_args['title'] = '<b>Sleep Totals</b><br>{}'.format(child)
    layout_args['xaxis']['title'] = 'Date'
    layout_args['xaxis']['rangeselector'] = utils.rangeselector_date()
    layout_args['yaxis']['title'] = 'Hours of sleep'

    fig = go.Figure({
        'data': [trace],
        'layout': go.Layout(**layout_args)
    })
    output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
    return utils.split_graph_output(output)


def _duration_string_short(duration):
    """Format a "short" duration string without seconds precision. This is
    intended to fit better in smaller spaces on a graph."""
    h, m, s = duration_parts(duration)
    return '{}h{}m'.format(h, m)


def sleep_pattern(child):
    """Create a graph showing blocked out periods of sleep during each day."""
    # TODO: Simplify this using the bar charts "base" property.
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
                year=start_time.year, month=start_time.month,
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
            color = 'rgb(35, 110, 150)'
        else:
            color = 'rgba(255, 255, 255, 0)'

    layout_args = utils.default_graph_layout_options()
    layout_args['margin']['b'] = 100

    layout_args['barmode'] = 'stack'
    layout_args['hovermode'] = 'closest'
    layout_args['title'] = '<b>Sleep Pattern</b><br>{}'.format(child)
    layout_args['height'] = 800

    layout_args['xaxis']['title'] = 'Date'
    layout_args['xaxis']['tickangle'] = -65
    layout_args['xaxis']['rangeselector'] = utils.rangeselector_date()

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
    return utils.split_graph_output(output)


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


def timeline(child, date):
    """Create a time-sorted dictionary for all events for a child."""
    min_date = date
    max_date = date.replace(hour=23, minute=59, second=59)
    events = []

    instances = DiaperChange.objects.filter(child=child).filter(
        time__range=(min_date, max_date)).order_by('-time')
    for instance in instances:
        events.append({
            'time': timezone.localtime(instance.time),
            'event': '{} had a diaper change.'.format(child.first_name),
            'model_name': instance.model_name,
        })

    instances = Feeding.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        events.append({
            'time': timezone.localtime(instance.start),
            'event': '{} started feeding.'.format(instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': '{} finished feeding.'.format(instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'end'
        })

    instances = Sleep.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        events.append({
            'time': timezone.localtime(instance.start),
            'event': '{} fell asleep.'.format(instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': '{} woke up.'.format(instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'end'
        })

    instances = TummyTime.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        events.append({
            'time': timezone.localtime(instance.start),
            'event': '{} started tummy time!'.format(
                instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': '{} finished tummy time.'.format(
                instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'end'
        })

    events.sort(key=lambda x: x['time'], reverse=True)

    return events
