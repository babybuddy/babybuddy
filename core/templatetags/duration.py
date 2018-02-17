# -*- coding: utf-8 -*-
from django import template

from core.utils import duration_parts, duration_string as d_string


register = template.Library()


@register.filter
def duration_string(duration, precision='s'):
    """
    Format a duration (e.g. "2 hours, 3 minutes, 35 seconds").
    :param duration: a timedetla instance.
    :param precision: the level of precision to return (h for hours, m for
                      minutes, s for seconds)
    :returns: a string representation of the duration.
    """
    if not duration:
        return ''
    try:
        return d_string(duration, precision)
    except (ValueError, TypeError):
        return ''


@register.filter
def hours(duration):
    """
    Return the "hours" portion of a duration.
    :param duration: a timedetla instance.
    :returns: an integer representing the number of hours in duration.
    """
    if not duration:
        return 0
    try:
        h, m, s = duration_parts(duration)
        return h
    except (ValueError, TypeError):
        return 0


@register.filter
def minutes(duration):
    """
    Return the "minutes" portion of a duration.
    :param duration: a timedetla instance.
    :returns: an integer representing the number of minutes in duration.
    """
    if not duration:
        return 0
    try:
        h, m, s = duration_parts(duration)
        return m
    except (ValueError, TypeError):
        return 0


@register.filter
def seconds(duration):
    """
    Return the "seconds" portion of a duration.
    :param duration: a timedetla instance.
    :returns: an integer representing the number of seconds in duration.
    """
    if not duration:
        return 0
    try:
        h, m, s = duration_parts(duration)
        return s
    except (ValueError, TypeError):
        return 0
