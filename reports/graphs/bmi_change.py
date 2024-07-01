# -*- coding: utf-8 -*-
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def bmi_change(objects):
    """
    Create a graph showing bmi over time.
    :param objects: a QuerySet of BMI instances.
    :returns: a tuple of the graph's html and javascript.
    """
    objects = objects.order_by("-date")

    trace = go.Scatter(
        name=_("BMI"),
        x=list(objects.values_list("date", flat=True)),
        y=list(objects.values_list("bmi", flat=True)),
        fill="tozeroy",
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("BMI") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("BMI")

    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
