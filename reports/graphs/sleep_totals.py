# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_parts

from reports import utils


def sleep_totals(instances):
    """
    Create a graph showing total time sleeping for each day.
    :param instances: a QuerySet of Sleep instances.
    :returns: a tuple of the graph's html and javascript.
    """
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
            totals[start.date()] += (
                end.replace(
                    year=start.year,
                    month=start.month,
                    day=start.day,
                    hour=23,
                    minute=59,
                    second=59,
                )
                - start
            )
            totals[end.date()] += end - start.replace(
                year=end.year, month=end.month, day=end.day, hour=0, minute=0, second=0
            )
        else:
            totals[start.date()] += instance.duration

    trace = go.Bar(
        name=_("Total sleep"),
        x=list(totals.keys()),
        y=[td.seconds / 3600 for td in totals.values()],
        hoverinfo="text",
        textposition="outside",
        text=[_duration_string_short(td) for td in totals.values()],
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Sleep Totals") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(trace.x)
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Hours of sleep")

    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)


def _duration_string_short(duration):
    """
    Format a "short" duration string without seconds precision. This is
    intended to fit better in smaller spaces on a graph.
    :returns: a string of the form XhXm.
    """
    h, m, s = duration_parts(duration)
    return "{}h{}m".format(h, m)
