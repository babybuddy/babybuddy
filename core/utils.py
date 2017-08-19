# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone


def filter_by_params(request, model, available_params):
    queryset = model.objects.all()

    for param in available_params:
        value = request.query_params.get(param, None)
        if value is not None:
            queryset = queryset.filter(**{param: value})

    return queryset


def timer_stop(timer_id, end=None):
    """Stop a timer instance by setting it's end field."""
    if not end:
        end = timezone.now()
    from .models import Timer
    timer_instance = Timer.objects.get(id=timer_id)
    timer_instance.end = end
    timer_instance.save()
