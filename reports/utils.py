# -*- coding: utf-8 -*-


def default_graph_layout_options():
    """
    Default layout options for all graphs.
    :returns: a dict of default options.
    """
    return {
        'paper_bgcolor': 'rgb(52, 58, 64)',
        'plot_bgcolor': 'rgb(52, 58, 64)',
        'font': {
            'color': 'rgba(255, 255, 255, 1)',
            # Bootstrap 4 font family.
            'family': '-apple-system, BlinkMacSystemFont, "Segoe UI", '
                      'Roboto, "Helvetica Neue", Arial, sans-serif, '
                      '"Apple Color Emoji", "Segoe UI Emoji", '
                      '"Segoe UI Symbol"',
            'size': 14,
        },
        'margin': {'b': 80, 't': 80},
        'xaxis': {
            'titlefont': {
                'color': 'rgba(255, 255, 255, 0.5)'
            },
            'gridcolor': 'rgba(0, 0, 0, 0.25)',
            'zerolinecolor': 'rgba(0, 0, 0, 0.5)'
        },
        'yaxis': {
            'titlefont': {
                'color': 'rgba(255, 255, 255, 0.5)'
            },
            'gridcolor': 'rgba(0, 0, 0, 0.25)',
            'zerolinecolor': 'rgba(0, 0, 0, 0.5)'
        }
    }


def rangeselector_date():
    """
    Graph date range selectors settings for 1w, 2w, 1m, 3m, and all.
    :returns: a dict of settings for the selectors.
    """
    return {
        'bgcolor': 'rgb(35, 149, 86)',
        'activecolor': 'rgb(25, 108, 62)',
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


def split_graph_output(output):
    """
    Split out of a Plotly graph in to html and javascript.
    :param output: a string of html and javascript comprising the graph.
    :returns: a tuple of the the graph's html and javascript.
    """
    html, js = output.split('<script')
    js = '<script' + js
    return html, js
