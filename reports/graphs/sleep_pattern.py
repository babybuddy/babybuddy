# -*- coding: utf-8 -*-
from collections import OrderedDict

from django.utils import timezone
from django.utils.translation import gettext as _

import pandas as pd
import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_string

from reports import utils


def sleep_pattern(instances):
    """
    Create a graph showing blocked out periods of sleep during each day.
    :param instances: a QuerySet of Sleep instances.
    :returns: a tuple of the the graph's html and javascript.
    """
    times = {}
    labels = {}

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

        if start_date not in times:
            times[start_date] = []
        if start_date not in labels:
            labels[start_date] = []

        # Check if the previous entry crossed midnight (see below).
        if adjustment:
            # Fake (0) entry to keep the color switching logic working.
            df_index = _add_sleep_entry(
                y_df, text_df, 0, adjustment['column'], 0)
            times[adjustment['column']].append(0)
            labels[adjustment['column']].append(0)

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
            times[adjustment['column']].append(
                adjustment['duration'].seconds/60)
            labels[adjustment['column']].append('Asleep {} ({} to {})'.format(
                duration_string(adjustment['duration']),
                adjustment['start_time'].strftime('%I:%M %p'),
                adjustment['end_time'].strftime('%I:%M %p')))

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
        # TODO: Fix this -- doesn't appear to work in the extra same way.
        if start_date not in times:
            last_end_time = start_time.replace(hour=0, minute=0, second=0)

        # Awake time.
        df_index = _add_sleep_entry(
            y_df,
            text_df,
            df_index,
            start_date,
            (start_time - last_end_time).seconds/60
        )
        times[start_date].append((start_time - last_end_time).seconds/60)
        labels[start_date].append(None)

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
        times[start_date].append(duration.seconds/60)
        labels[start_date].append('Asleep {} ({} to {})'.format(
            duration_string(duration),
            start_time.strftime('%I:%M %p'),
            end_time.strftime('%I:%M %p')))

        # Update the previous entry duration if an offset change occurred.
        # This can happen when an entry crosses a daylight savings time change.
        # TODO: Reimplement this functionality.
        # if start_time.utcoffset() != end_time.utcoffset():
        #     diff = start_time.utcoffset() - end_time.utcoffset()
        #     duration -= timezone.timedelta(seconds=diff.seconds)
        #     y_df.at[df_index - 1, start_date] = duration.seconds/60

        last_end_time = end_time

    dates = list(times.keys())
    traces = []
    color = 'rgba(255, 255, 255, 0)'

    # Set iterator and determine maximum iteration for dates.
    i = 0
    max_i = 0
    for date_times in times.values():
        max_i = max(len(date_times), max_i)
    while i < max_i:
        y = {}
        text = {}
        for date in times.keys():
            try:
                y[date] = times[date][i]
                text[date] = labels[date][i]
            except IndexError:
                y[date] = None
                text[date] = None
        i += 1
        traces.append(go.Bar(
            x=dates,
            y=list(y.values()),
            text=list(text.values()),
            hoverinfo='text',
            marker={'color': color},
            marker_line_width=0,
            showlegend=False,
        ))
        if color == 'rgba(255, 255, 255, 0)':
            color = 'rgb(35, 110, 150)'
        else:
            color = 'rgba(255, 255, 255, 0)'

    layout_args = utils.default_graph_layout_options()
    layout_args['margin']['b'] = 100

    layout_args['barmode'] = 'stack'
    layout_args['bargap'] = 0
    layout_args['hovermode'] = 'closest'
    layout_args['title'] = _('<b>Sleep Pattern</b>')
    layout_args['height'] = 800

    layout_args['xaxis']['title'] = _('Date')
    layout_args['xaxis']['tickangle'] = -65
    layout_args['xaxis']['rangeselector'] = utils.rangeselector_date()

    start = timezone.localtime().strptime('12:00 AM', '%I:%M %p')
    ticks = OrderedDict()
    ticks[0] = start.strftime('%I:%M %p')
    for i in range(30, 60*24, 30):
        ticks[i] = (start + timezone.timedelta(minutes=i)).strftime('%I:%M %p')

    layout_args['yaxis']['title'] = _('Time of day')
    layout_args['yaxis']['range'] = [0, 24*60]
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
    """
    Create a duration and text description entry in a DataFrame and return
    the next index on success.
    :param y_df: the y values DataFrame.
    :param text_df: the text values DataFrame.
    :param index: the index to target in both y_df and text_df.
    :param column: the column (date) to make the entry in.
    :param duration: the duration of the entry.
    :param text: text to go with the entry (displays on graph hover).
    :return: the next index of the DataFrames.
    """
    if column not in y_df:
        y_df.assign(**{column: 0 in range(0, len(y_df.index))})
        text_df.assign(**{column: 0 in range(0, len(text_df.index))})
        index = 0

    y_df.at[index, column] = duration
    text_df.at[index, column] = text
    return index + 1
