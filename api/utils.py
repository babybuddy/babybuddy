# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def filter_by_params(request, model, available_params):
    """Filters all instances of a model based on request parameters.
    """
    queryset = model.objects.all()

    for param in available_params:
        value = request.query_params.get(param, None)
        if value is not None:
            queryset = queryset.filter(**{param: value})

    return queryset
