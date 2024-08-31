# -*- coding: utf-8 -*-
from django.db.models import Count, Case, When
from django.db.models.functions import TruncDate
from django.utils.translation import gettext as _
from django.utils.translation import get_language

import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_parts

from reports import utils


def diaperchange_intervals(changes):
    """
    Create a graph showing intervals of diaper changes.
    :param changes: a QuerySet of Diaper Change instances.
    :returns: a tuple of the graph's html and javascript.
    """

    changes = changes.order_by("time")
    intervals = []
    intervals_solid = []
    intervals_wet = []
    last_change = changes.first()
    for change in changes[1:]:
        interval = change.time - last_change.time
        if interval.total_seconds() > 0:
            intervals.append(interval)
            if change.solid:
                intervals_solid.append(interval)
            if change.wet:
                intervals_wet.append(interval)
        last_change = change

    trace_solid = go.Scatter(
        name=_("Solid"),
        line=dict(shape="spline"),
        x=list(changes.values_list("time", flat=True))[1:],
        y=[i.total_seconds() / 3600 for i in intervals_solid],
        hoverinfo="text",
        text=[_duration_string_hms(i) for i in intervals_solid],
    )

    trace_wet = go.Scatter(
        name=_("Wet"),
        line=dict(shape="spline"),
        x=list(changes.values_list("time", flat=True))[1:],
        y=[i.total_seconds() / 3600 for i in intervals_wet],
        hoverinfo="text",
        text=[_duration_string_hms(i) for i in intervals_wet],
    )

    trace_total = go.Scatter(
        name=_("Total"),
        line=dict(shape="spline"),
        x=list(changes.values_list("time", flat=True))[1:],
        y=[i.total_seconds() / 3600 for i in intervals],
        hoverinfo="text",
        text=[_duration_string_hms(i) for i in intervals],
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Diaper Change Intervals") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(trace_total.x)
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Interval (hours)")

    fig = go.Figure(
        {
            "data": [trace_solid, trace_wet, trace_total],
            "layout": go.Layout(**layout_args),
        }
    )
    output = plotly.plot(
        fig,
        output_type="div",
        include_plotlyjs=False,
        config={"locale": get_language()},
    )
    return utils.split_graph_output(output)


def _duration_string_hms(duration):
    """
    Format a duration string with hours, minutes and seconds. This is
    intended to fit better in smaller spaces on a graph.
    :returns: a string of the form Xm.
    """
    h, m, s = duration_parts(duration)
    return "{}h{}m{}s".format(h, m, s)
