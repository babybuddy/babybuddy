# -*- coding: utf-8 -*-
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def medication_frequency(instances):
    """
    Create a graph showing frequency of medication instances over time.

    :param instances: a QuerySet of Medication instances.
    :returns: a tuple of the graph's html and javascript.
    """
    totals = (
        instances.annotate(date=TruncDate("time"))
        .values("date")
        .annotate(count=Count("id"))
        .order_by("date")
    )

    if not totals:
        return None, None

    trace = go.Scatter(
        name=_("Frequency"),
        line=dict(shape="spline"),
        x=list(totals.values_list("date", flat=True)),
        y=list(totals.values_list("count", flat=True)),
        fill="tozeroy",
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Medication frequency") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(trace.x)
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Number of medications")

    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
