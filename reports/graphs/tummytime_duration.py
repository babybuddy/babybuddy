# -*- coding: utf-8 -*-
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from core.utils import duration_parts

from reports import utils


def tummytime_duration(instances):
    """
    Create a graph showing total duration of tummy time instances per day.

    :param instances: a QuerySet of TummyTime instances.
    :returns: a tuple of the graph's html and javascript.
    """
    totals = (
        instances.annotate(date=TruncDate("start"))
        .values("date")
        .annotate(count=Count("id"))
        .annotate(sum=Sum("duration"))
        .order_by("-date")
    )

    sums = []
    for total in totals:
        sums.append(total["sum"])

    trace_avg = go.Bar(
        name=_("Total duration"),
        x=list(totals.values_list("date", flat=True)),
        y=[td.seconds / 60 for td in sums],
        hoverinfo="text",
        text=[_duration_string_ms(td) for td in sums],
    )
    trace_count = go.Scatter(
        name=_("Number of sessions"),
        mode="markers",
        x=list(totals.values_list("date", flat=True)),
        y=list(totals.values_list("count", flat=True)),
        yaxis="y2",
        hoverinfo="y",
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Total Tummy Time Durations") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(
        trace_avg.x, 35000000
    )
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Total duration (minutes)")
    layout_args["yaxis2"] = dict(layout_args["yaxis"])
    layout_args["yaxis2"]["title"] = _("Number of sessions")
    layout_args["yaxis2"]["overlaying"] = "y"
    layout_args["yaxis2"]["side"] = "right"

    fig = go.Figure(
        {"data": [trace_avg, trace_count], "layout": go.Layout(**layout_args)}
    )
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)


def _duration_string_ms(duration):
    """
    Format a "short" duration string with only minutes and seconds. This is
    intended to fit better in smaller spaces on a graph.
    :returns: a string of the form Xm.
    """
    h, m, s = duration_parts(duration)
    if h > 0:
        return "{}h{}m{}s".format(h, m, s)
    else:
        return "{}m{}s".format(m, s)
