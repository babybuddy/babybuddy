# -*- coding: utf-8 -*-
from django.db.models import Count, Case, When
from django.db.models.functions import TruncDate
from django.utils.translation import gettext as _
from django.utils.translation import get_language

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def diaperchange_types(changes):
    """
    Create a graph showing types of totals for diaper changes.
    :param changes: a QuerySet of Diaper Change instances.
    :returns: a tuple of the graph's html and javascript.
    """
    changes = (
        changes.annotate(date=TruncDate("time"))
        .values("date")
        .annotate(wet_count=Count(Case(When(wet=True, then=1))))
        .annotate(solid_count=Count(Case(When(solid=True, then=1))))
        .annotate(total=Count("id"))
        .order_by("-date")
    )

    solid_trace = go.Scatter(
        mode="markers",
        name=_("Solid"),
        x=list(changes.values_list("date", flat=True)),
        y=list(changes.values_list("solid_count", flat=True)),
    )
    wet_trace = go.Scatter(
        mode="markers",
        name=_("Wet"),
        x=list(changes.values_list("date", flat=True)),
        y=list(changes.values_list("wet_count", flat=True)),
    )
    total_trace = go.Scatter(
        name=_("Total"),
        x=list(changes.values_list("date", flat=True)),
        y=list(changes.values_list("total", flat=True)),
    )

    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Diaper Change Types") + "</b>"
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["type"] = "date"
    layout_args["xaxis"]["autorange"] = True
    layout_args["xaxis"]["autorangeoptions"] = utils.autorangeoptions(total_trace.x)
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Number of changes")

    fig = go.Figure(
        {
            "data": [solid_trace, wet_trace, total_trace],
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
