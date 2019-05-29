# -*- coding: utf-8 -*-
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils.translation import gettext as _

import plotly.offline as plotly
import plotly.graph_objs as go

from reports import utils


def feeding_amounts(instances):
    """
    Create a graph showing daily feeding amounts over time.
    :param instances: a QuerySet of Feeding instances.
    :returns: a tuple of the the graph's html and javascript.
    """
    totals = instances.annotate(date=TruncDate('start')) \
        .values('date') \
        .annotate(sum=Sum('amount')) \
        .order_by('-date')

    dates = [value['date'] for value in totals.values('date')]
    amounts = [value['amount'] or 0 for value in totals.values('amount')]

    trace = go.Bar(
        name=_('Total feeding amount'),
        x=dates,
        y=amounts,
        hoverinfo='text',
        textposition='outside',
        text=amounts
    )

    layout_args = utils.default_graph_layout_options()
    layout_args['title'] = _('<b>Total Feeding Amounts</b>')
    layout_args['xaxis']['title'] = _('Date')
    layout_args['xaxis']['rangeselector'] = utils.rangeselector_date()
    layout_args['yaxis']['title'] = _('Feeding amount')

    fig = go.Figure({
        'data': [trace],
        'layout': go.Layout(**layout_args)
    })
    output = plotly.plot(fig, output_type='div', include_plotlyjs=False)
    return utils.split_graph_output(output)
