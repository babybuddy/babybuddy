# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_parts

from reports import utils


def awake_times(instances):
    """
    Create a graph showing average awake times for each day.
    :param instances: a QuerySet of Sleep instances.
    :returns: a tuple of the graph's html and javascript.
    """
    awake_times = {}
    for i, instance in enumerate(instances):
        if i > 0:
            prev_instance = instances[i-1]
            start = timezone.localtime(instance.start)
            end = timezone.localtime(prev_instance.end)
            if start.date() not in awake_times.keys():
                awake_times[start.date()] = []
            
            awake_duration = start - end
            if awake_duration.total_seconds() > 0:
                awake_times[start.date()].append(awake_duration)

    dates = sorted(awake_times.keys())
    avg_awake_times = []
    for date in dates:
        avg_awake_times.append(sum(awake_times[date], timezone.timedelta(0)) / len(awake_times[date]))


    trace = go.Scatter(
        name=_("Average awake time"),
        x=dates,
        y=[td.seconds / 3600 for td in avg_awake_times],
        hoverinfo="text",
        text=[_duration_string_short(td) for td in avg_awake_times],
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Average Awake Times") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(trace.x)
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Hours awake")

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
