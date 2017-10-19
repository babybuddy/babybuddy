# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def default_graph_layout_options():
    """Default layout options for all graphs.
    """
    return {
        'font': {
            'color': 'rgba(0, 0, 0, 1)',
            # Bootstrap 4 font family.
            'family': '-apple-system, BlinkMacSystemFont, "Segoe UI", '
                      'Roboto, "Helvetica Neue", Arial, sans-serif, '
                      '"Apple Color Emoji", "Segoe UI Emoji", '
                      '"Segoe UI Symbol"',
            'size': 14,
        },
        'margin': {'b': 40, 't': 80},
        'xaxis': {
            'titlefont': {
                'color': 'rgba(0, 0, 0, 0.54)'
            }
        },
        'yaxis': {
            'titlefont': {
                'color': 'rgba(0, 0, 0, 0.54)'
            }
        }
    }


def rangeselector_date():
    """Graph date range selectors settings for 1w, 2w, 1m, 3m, and all.
    """
    return {
        'buttons': [
            {
                'count': 7,
                'label': '1w',
                'step': 'day',
                'stepmode': 'backward'
            },
            {
                'count': 14,
                'label': '2w',
                'step': 'day',
                'stepmode': 'backward'
            },
            {
                'count': 1,
                'label': '1m',
                'step': 'month',
                'stepmode': 'backward'
            },
            {
                'count': 3,
                'label': '3m',
                'step': 'month',
                'stepmode': 'backward'
            },
            {
                'step': 'all'
            }
        ]
    }


def rangeslider():
    """A range slider.
    """
    return {

    }


def split_graph_output(output):
    """Split out of a Plotly graph in to html and javascript.
    """
    html, javascript = output.split('<script')
    javascript = '<script' + javascript
    return html, javascript
