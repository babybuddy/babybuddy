# -*- coding: utf-8 -*-
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def head_circumference_change(objects):
    """
    Create a graph showing head_circumference over time.
    :param objects: a QuerySet of Head Circumference instances.
    :returns: a tuple of the graph's html and javascript.
    """
    objects = objects.order_by("-date")

    trace = go.Scatter(
        name=_("Head Circumference"),
        x=list(objects.values_list("date", flat=True)),
        y=list(objects.values_list("head_circumference", flat=True)),
        fill="tozeroy",
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Head Circumference") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Head Circumference")

    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
