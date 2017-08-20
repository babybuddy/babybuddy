# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

from django import template


register = template.Library()


@register.filter
def duration_string(duration):
    h, m, s = _get_hms(duration)

    duration = ''
    if h > 0:
        duration = '{} hour{}'.format(h, 's' if h > 1 else '')
    if m > 0:
        duration += '{}{} minute{}'.format(
            '' if duration is '' else ', ', m, 's' if m > 1 else '')
    if s > 0:
        duration += '{}{} second{}'.format(
            '' if duration is '' else ', ', s, 's' if s > 1 else '')

    return duration


@register.filter
def hours(duration):
    h, m, s = _get_hms(duration)
    return h


@register.filter
def minutes(duration):
    h, m, s = _get_hms(duration)
    return m


@register.filter
def seconds(duration):
    h, m, s = _get_hms(duration)
    return s


def _get_hms(duration):
    """Get hours, minutes and seconds from a timedelta."""
    if not isinstance(duration, timedelta):
        return 0, 0, 0
    h, remainder = divmod(duration.seconds, 3600)
    m, s = divmod(remainder, 60)
    return h, m, s
