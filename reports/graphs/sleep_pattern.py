# -*- coding: utf-8 -*-
from collections import OrderedDict

from django.utils import timezone, formats
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go
import plotly.colors as colors

from core.utils import duration_string

from reports import utils

from datetime import timedelta

ASLEEP_COLOR = "rgb(35, 110, 150)"
AWAKE_COLOR = colors.DEFAULT_PLOTLY_COLORS[2]


def sleep_pattern(sleeps):
    """
    Create a graph showing blocked out periods of sleep during each day.
    :param sleeps: a QuerySet of Sleep instances.
    :returns: a tuple of the graph's html and javascript.
    """
    last_end_time = None
    adjustment = None

    first_day = timezone.localtime(sleeps.first().start)
    last_day = timezone.localtime(sleeps.last().end)
    days = _init_days(first_day, last_day)

    for sleep in sleeps:
        start_time = timezone.localtime(sleep.start)
        end_time = timezone.localtime(sleep.end)
        start_date = start_time.date().isoformat()
        end_date = end_time.date().isoformat()
        duration = sleep.duration

        # Check if the previous entry crossed midnight (see below).
        if adjustment:
            _add_adjustment(adjustment, days)
            last_end_time = timezone.localtime(adjustment["end_time"])
            adjustment = None

        # If the dates do not match, set up an adjustment for the next day.
        if end_time.date() != start_time.date():
            adj_start_time = end_time.replace(hour=0, minute=0, second=0)
            adjustment = {
                "column": end_date,
                "start_time": adj_start_time,
                "end_time": end_time,
                "duration": end_time - adj_start_time,
            }

            # Adjust end_time for the current entry.
            end_time = end_time.replace(
                year=start_time.year,
                month=start_time.month,
                day=start_time.day,
                hour=23,
                minute=59,
                second=0,
            )
            duration = end_time - start_time

        if last_end_time:
            if last_end_time.date() < start_time.date():
                # Awake across midnight
                days[last_end_time.date().isoformat()].append(
                    _awake_event(
                        last_end_time,
                        last_end_time.replace(
                            hour=23,
                            minute=59,
                            second=0,
                        ),
                    )
                )

                last_end_time = start_time.replace(hour=0, minute=0, second=0)

        if not last_end_time:
            last_end_time = start_time.replace(hour=0, minute=0, second=0)

        # Awake time.
        days[start_date].append(_awake_event(last_end_time, start_time))

        # Asleep time.
        days[start_date].append(
            {
                "time": duration.seconds / 60,
                "label": _format_asleep_label(duration, start_time, end_time),
            }
        )

        # Update the previous entry duration if an offset change occurred.
        # This can happen when an entry crosses a daylight savings time change.
        if start_time.utcoffset() != end_time.utcoffset():
            diff = start_time.utcoffset() - end_time.utcoffset()
            duration -= timezone.timedelta(seconds=diff.seconds)
            yesterday = end_time - timezone.timedelta(days=1)
            yesterday = yesterday.date().isoformat()
            days[yesterday][len(days[yesterday]) - 1] = {
                "time": duration.seconds / 60,
                "label": _format_asleep_label(duration, start_time, end_time),
            }

        last_end_time = end_time

    # Handle any left over adjustment (if the last entry crossed midnight).
    if adjustment:
        _add_adjustment(adjustment, days)

    # Create dates for x-axis using a 12:00:00 time to ensure correct
    # positioning of bars (covering entire day).
    dates = []
    for time in list(days.keys()):
        dates.append("{} 12:00:00".format(time))

    traces = []
    color = AWAKE_COLOR

    # Set iterator and determine maximum iteration for dates.
    i = 0
    max_i = 0
    for date_times in days.values():
        max_i = max(len(date_times), max_i)
    while i < max_i:
        y = {}
        text = {}
        for date in days.keys():
            try:
                y[date] = days[date][i]["time"]
                text[date] = days[date][i]["label"]
            except IndexError:
                y[date] = None
                text[date] = None
        i += 1
        traces.append(
            go.Bar(
                x=dates,
                y=list(y.values()),
                hovertext=list(text.values()),
                # `hoverinfo` is deprecated but if we use the new `hovertemplate`
                # the "filler" areas for awake time get a hover that says "null"
                # and there is no way to prevent this currently with Plotly.
                hoverinfo="text",
                marker={"color": color},
                showlegend=False,
            )
        )
        if color == AWAKE_COLOR:
            color = ASLEEP_COLOR
        else:
            color = AWAKE_COLOR

    layout_args = utils.default_graph_layout_options()
    layout_args["margin"]["b"] = 100

    layout_args["barmode"] = "stack"
    layout_args["bargap"] = 0
    layout_args["hovermode"] = "closest"
    layout_args["title"] = "<b>" + _("Sleep Pattern") + "</b>"
    layout_args["height"] = 800

    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["tickangle"] = -65
    layout_args["xaxis"]["tickformat"] = "%b %e\n%Y"
    layout_args["xaxis"]["ticklabelmode"] = "period"
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()

    start = timezone.localtime().strptime("12:00 AM", "%I:%M %p")
    ticks = OrderedDict()
    ticks[0] = start.strftime("%I:%M %p")
    for i in range(0, 60 * 24, 30):
        ticks[i] = formats.time_format(
            start + timezone.timedelta(minutes=i), "TIME_FORMAT"
        )

    layout_args["yaxis"]["title"] = _("Time of day")
    layout_args["yaxis"]["range"] = [24 * 60, 0]
    layout_args["yaxis"]["tickmode"] = "array"
    layout_args["yaxis"]["tickvals"] = list(ticks.keys())
    layout_args["yaxis"]["ticktext"] = list(ticks.values())
    layout_args["yaxis"]["tickfont"] = {"size": 10}

    fig = go.Figure({"data": traces, "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)


def _init_days(first_day, last_day):
    period = (last_day.date() - first_day.date()).days + 1

    def new_day(d):
        return (first_day + timedelta(days=d)).date().isoformat()

    return {new_day(day): [] for day in range(period)}


def _add_adjustment(adjustment, days):
    """
    Adds "adjustment" data for entries that cross midnight.
    :param adjustment: Column, start time, end time, and duration of entry.
    :param blocks: List of days
    """
    column = adjustment.pop("column")
    if not column in days:
        days[column] = []
    # Fake (0) entry to keep the color switching logic working.
    days[column].append({"time": 0, "label": 0})

    # Real adjustment entry.
    days[column].append(
        {
            "time": adjustment["duration"].seconds / 60,
            "label": _format_asleep_label(**adjustment),
        }
    )


def _awake_event(last_end_time, next_start_time):
    awake_duration = next_start_time - last_end_time
    return {
        "time": awake_duration.seconds / 60,
        "label": _format_awake_label(awake_duration, last_end_time, next_start_time),
    }


def _format_asleep_label(duration, start_time, end_time):
    return _format_label("Asleep", duration, start_time, end_time)


def _format_awake_label(duration, start_time, end_time):
    return _format_label("Awake", duration, start_time, end_time)


def _format_label(state, duration, start_time, end_time):
    """
    Formats a time block label.
    :param state: Asleep or awake
    :param duration: Duration.
    :param start_time: Start time.
    :param end_time: End time.
    :return: Formatted string with duration, start, and end time.
    """
    return "{} {} ({} to {})".format(
        state,
        duration_string(duration),
        formats.time_format(start_time, "TIME_FORMAT"),
        formats.time_format(end_time, "TIME_FORMAT"),
    )
