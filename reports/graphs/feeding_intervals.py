# -*- coding: utf-8 -*-
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_parts

from reports import utils


def feeding_intervals(instances):
    """
    Create a graph showing intervals of feeding instances over time.

    :param instances: a QuerySet of Feeding instances.
    :returns: a tuple of the the graph's html and javascript.
    """
    totals = instances.annotate(count=Count("id")).order_by("start")

    intervals = []
    last_feeding = totals.first()
    for feeding in totals[1:]:
        interval = feeding.start - last_feeding.start
        if interval.seconds > 0:
            intervals.append(interval)
        last_feeding = feeding

    trace_avg = go.Scatter(
        name=_("Interval"),
        line=dict(shape="spline"),
        x=list(totals.values_list("start", flat=True)),
        y=[i.seconds / 60 for i in intervals],
        hoverinfo="text",
        text=[_duration_string_hms(i) for i in intervals],
    )
    trace_count = go.Scatter(
        name=_("Total feedings"),
        mode="markers",
        x=list(totals.values_list("start", flat=True)),
        y=list(totals.values_list("count", flat=True)),
        yaxis="y2",
        hoverinfo="y",
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = _("<b>Feeding interval</b>")
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Feeding interval (minutes)")
    layout_args["yaxis2"] = dict(layout_args["yaxis"])
    layout_args["yaxis2"]["title"] = _("Number of feedings")
    layout_args["yaxis2"]["overlaying"] = "y"
    layout_args["yaxis2"]["side"] = "right"

    fig = go.Figure(
        {"data": [trace_avg, trace_count], "layout": go.Layout(**layout_args)}
    )
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)


def _duration_string_hms(duration):
    """
    Format a duration string with hours, minutes and seconds. This is
    intended to fit better in smaller spaces on a graph.
    :returns: a string of the form Xm.
    """
    h, m, s = duration_parts(duration)
    return "{}h{}m{}s".format(h, m, s)
