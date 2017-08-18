# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from math import floor

from django.utils import timezone


def duration_string(start, end, short=False):
    diff = end - start
    h = floor(diff.seconds / 3600)
    m = floor((diff.seconds - h * 3600) / 60)
    s = diff.seconds % 60

    duration = ''
    if short:
        duration = '{}h {}m {}s'.format(h, m, s)
    else:
        if h > 0:
            duration = '{} hour{}'.format(h, 's' if h > 1 else '')
        if m > 0:
            duration += '{}{} minute{}'.format(
                '' if duration is '' else ', ', m, 's' if m > 1 else '')
        if s > 0:
            duration += '{}{} second{}'.format(
                '' if duration is '' else ', ', s, 's' if s > 1 else '')

    return duration


def filter_by_params(request, model, available_params):
    queryset = model.objects.all()

    for param in available_params:
        value = request.query_params.get(param, None)
        if value is not None:
            queryset = queryset.filter(**{param: value})

    return queryset


# Stop a timer instance by setting it's end field.
def timer_stop(timer_id, end=None):
    if not end:
        end = timezone.now()
    from .models import Timer
    timer_instance = Timer.objects.get(id=timer_id)
    timer_instance.end = end
    timer_instance.save()
