# -*- coding: utf-8 -*-
from collections import OrderedDict

from django.utils import timezone, formats
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_string

from reports import utils

from datetime import timedelta

FEEDING_COLOR = "rgb(35, 110, 150)"
NOT_FEEDING_COLOR = "rgba(255, 255, 255, 0)"


def feeding_pattern(feedings):
    """
    Create a graph showing blocked out periods of feeding during each day.
    :param feedings: a QuerySet of Feeding instances.
    :returns: a tuple of the graph's html and javascript.
    """
    last_end_time = None
    adjustment = None

    first_day = timezone.localtime(feedings.first().start)
    last_day = timezone.localtime(feedings.last().end)
    days = _init_days(first_day, last_day)

    for feeding in feedings:
        start_time = timezone.localtime(feeding.start)
        end_time = timezone.localtime(feeding.end)
        start_date = start_time.date().isoformat()
        end_date = end_time.date().isoformat()
        duration = feeding.duration

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
                # Not feeding across midnight
                last_date = last_end_time.date().isoformat()
                last_midnight = last_end_time.replace(hour=23, minute=59)
                days[last_date].append(
                    {
                        "time": (last_midnight - last_end_time).seconds / 60,
                        "label": None,
                    }
                )
                last_end_time = start_time.replace(hour=0, minute=0, second=0)

        if not last_end_time:
            last_end_time = start_time.replace(hour=0, minute=0, second=0)

        # Not feeding time.
        days[start_date].append(
            {"time": (start_time - last_end_time).seconds / 60, "label": None}
        )

        # Feeding time.
        days[start_date].append(
            {
                "time": duration.seconds / 60,
                "label": _format_label(duration, start_time, end_time),
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
                "label": _format_label(duration, start_time, end_time),
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
    color = NOT_FEEDING_COLOR

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
        if color == NOT_FEEDING_COLOR:
            color = FEEDING_COLOR
        else:
            color = NOT_FEEDING_COLOR

    layout_args = utils.default_graph_layout_options()
    layout_args["margin"]["b"] = 100

    layout_args["barmode"] = "stack"
    layout_args["bargap"] = 0
    layout_args["hovermode"] = "closest"
    layout_args["title"] = "<b>" + _("Feeding Pattern") + "</b>"
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
            "label": _format_label(**adjustment),
        }
    )


def _format_label(duration, start_time, end_time):
    """
    Formats a time block label.
    :param duration: Duration.
    :param start_time: Start time.
    :param end_time: End time.
    :return: Formatted string with duration, start, and end time.
    """
    return "Feeding {} ({} to {})".format(
        duration_string(duration),
        formats.time_format(start_time, "TIME_FORMAT"),
        formats.time_format(end_time, "TIME_FORMAT"),
    )
