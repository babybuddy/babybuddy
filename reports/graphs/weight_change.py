# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from django.utils.translation import gettext as _
from django.db.models.manager import BaseManager

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def weight_change(
    actual_weights: BaseManager,
    percentile_weights: BaseManager,
    birthday: datetime,
    due_date: datetime = None,
):
    """
    Create a graph showing weight over time.
    :param actual_weights: a QuerySet of Weight instances.
    :param percentile_weights: a QuerySet of Weight Percentile instances.
    :param birthday: a datetime of the child's birthday
    :param due_date: an optional datetime of the child's due date. When set and
        later than the birthday (i.e. the child was born preterm), percentile
        curves are anchored to the due date so they are plotted against
        corrected age.
    :returns: a tuple of the graph's html and javascript.
    """
    actual_weights = actual_weights.order_by("-date")

    # When a due date later than the birthday is recorded the child was born
    # preterm; anchor the percentile curves to the due date so that they line
    # up with corrected age. The actual measurements remain on their true
    # dates.
    correct_for_prematurity = bool(due_date and due_date > birthday)
    percentile_anchor = due_date if correct_for_prematurity else birthday

    weighing_dates: list[datetime] = list(actual_weights.values_list("date", flat=True))
    measured_weights = list(actual_weights.values_list("weight", flat=True))

    actual_weights_trace = go.Scatter(
        name=_("Weight"),
        x=weighing_dates,
        y=measured_weights,
        fill="tozeroy",
        mode="lines+markers",
    )

    if percentile_weights:
        dates = list(
            map(
                lambda age: percentile_anchor + age,
                percentile_weights.values_list("age_in_days", flat=True),
            )
        )

        # reduce percentile data xrange to end 1 day after last weigh in for formatting purposes
        # https://github.com/babybuddy/babybuddy/pull/708#discussion_r1332335789
        # When anchored to the due date the last weigh in may fall before the
        # first percentile point, so slice by comparison rather than index.
        last_date_for_percentiles = min(max(dates), max(weighing_dates))
        visible_points = sum(1 for date in dates if date <= last_date_for_percentiles)
        dates = dates[: max(visible_points, 1)]

        percentile_weight_3_trace = go.Scatter(
            name=_("P3"),
            x=dates,
            y=list(percentile_weights.values_list("p3_weight", flat=True)),
            line={"color": "red"},
        )
        percentile_weight_15_trace = go.Scatter(
            name=_("P15"),
            x=dates,
            y=list(percentile_weights.values_list("p15_weight", flat=True)),
            line={"color": "orange"},
        )
        percentile_weight_50_trace = go.Scatter(
            name=_("P50"),
            x=dates,
            y=list(percentile_weights.values_list("p50_weight", flat=True)),
            line={"color": "green"},
        )
        percentile_weight_85_trace = go.Scatter(
            name=_("P85"),
            x=dates,
            y=list(percentile_weights.values_list("p85_weight", flat=True)),
            line={"color": "orange"},
        )
        percentile_weight_97_trace = go.Scatter(
            name=_("P97"),
            x=dates,
            y=list(percentile_weights.values_list("p97_weight", flat=True)),
            line={"color": "red"},
        )

    data = [
        actual_weights_trace,
    ]
    layout_args = utils.default_graph_layout_options()
    layout_args["barmode"] = "stack"
    layout_args["title"] = "<b>" + _("Weight") + "</b>"
    if correct_for_prematurity:
        layout_args["title"] += (
            "<br><sup>" + _("Percentiles plotted by corrected age") + "</sup>"
        )
    layout_args["xaxis"]["title"] = _("Date")
    layout_args["xaxis"]["rangeselector"] = utils.rangeselector_date()
    layout_args["yaxis"]["title"] = _("Weight")
    if percentile_weights:
        # zoom in on the relevant dates
        layout_args["xaxis"]["range"] = [
            birthday,
            max(weighing_dates) + timedelta(days=1),
        ]
        layout_args["yaxis"]["range"] = [0, max(measured_weights) * 1.5]
        data.extend(
            [
                percentile_weight_97_trace,
                percentile_weight_85_trace,
                percentile_weight_50_trace,
                percentile_weight_15_trace,
                percentile_weight_3_trace,
            ]
        )

    fig = go.Figure({"data": data, "layout": go.Layout(**layout_args)})
    output = plotly.plot(fig, output_type="div", include_plotlyjs=False)
    return utils.split_graph_output(output)
