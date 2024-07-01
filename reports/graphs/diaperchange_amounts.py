# -*- coding: utf-8 -*-
from django.utils import timezone
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def diaperchange_amounts(instances):
    """
    Create a graph showing daily diaper change amounts over time.
    :param instances: a QuerySet of DiaperChange instances.
    :returns: a tuple of the graph's html and javascript.
    """
    totals = {}
    for instance in instances:
        time_local = timezone.localtime(instance.time)
        date = time_local.date()
        if date not in totals.keys():
            totals[date] = 0
        totals[date] += instance.amount or 0

    amounts = [round(amount, 2) for amount in totals.values()]
    trace = go.Bar(
        name=_("Diaper change amount"),
        x=list(totals.keys()),
        y=amounts,
        hoverinfo="text",
        textposition="outside",
        text=amounts,
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["title"] = "<b>" + _("Diaper Change Amounts") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Change amount")

    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
