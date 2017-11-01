# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from core.utils import duration_parts, duration_string as d_string


register = template.Library()


@register.filter
def duration_string(duration, precision='s'):
    """Format a duration (e.g. "2 hours, 3 minutes, 35 seconds")."""
    if not duration:
        return ''
    try:
        return d_string(duration, precision)
    except (ValueError, TypeError):
        return ''


@register.filter
def hours(duration):
    """Return "hours" portion of a duration."""
    if not duration:
        return 0
    try:
        h, m, s = duration_parts(duration)
        return h
    except (ValueError, TypeError):
        return 0


@register.filter
def minutes(duration):
    """Return "minutes" portion of a duration."""
    if not duration:
        return 0
    try:
        h, m, s = duration_parts(duration)
        return m
    except (ValueError, TypeError):
        return 0


@register.filter
def seconds(duration):
    """Return "seconds" portion of a duration."""
    if not duration:
        return 0
    try:
        h, m, s = duration_parts(duration)
        return s
    except (ValueError, TypeError):
        return 0
