# -*- coding: utf-8 -*-
from django import template

from core import utils


register = template.Library()


@register.filter
def child_age_string(birth_date):
    """
    Format a Child's age with monkey-patched timesince.
    :param birth_date: datetime instance
    :return: a string representation of time since `birth_date`.
    """
    if not birth_date:
        return ''
    try:
        return utils.child_age_string(birth_date)
    except (ValueError, TypeError):
        return ''


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
        return utils.duration_string(duration, precision)
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
        h, m, s = utils.duration_parts(duration)
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
        h, m, s = utils.duration_parts(duration)
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
        h, m, s = utils.duration_parts(duration)
        return s
    except (ValueError, TypeError):
        return 0
