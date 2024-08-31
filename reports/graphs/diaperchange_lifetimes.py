# -*- coding: utf-8 -*-
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def diaperchange_lifetimes(changes):
    """
    Create a graph showing how long diapers last (time between changes).
    :param changes: a QuerySet of Diaper Change instances.
    :returns: a tuple of the graph's html and javascript.
    """
    changes = changes.order_by("time")
    durations = []
    last_change = changes.first()
    for change in changes[1:]:
        duration = change.time - last_change.time
        if duration.seconds > 0:
            durations.append(duration)
        last_change = change

    trace = go.Box(
        y=[round(d.seconds / 3600, 2) for d in durations],
        name=_("Changes"),
        jitter=0.3,
        pointpos=-1.8,
        boxpoints="all",
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["height"] = 800
    layout_args["title"] = "<b>" + _("Diaper Lifetimes") + "</b>"
    layout_args["yaxis"]["title"] = _("Time between changes (hours)")
    layout_args["yaxis"]["zeroline"] = False
    layout_args["yaxis"]["dtick"] = 1

    fig = go.Figure({"data": [trace], "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
