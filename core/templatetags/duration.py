# -*- coding: utf-8 -*-
import datetime

from django import template
from django.utils import timesince, timezone
from django.utils.translation import gettext as _

from core import utils


register = template.Library()


@register.filter
def child_age_string(birth_date):
    """
    Format a Child's age with a timeunit depth of 1.
    :param birth_date: datetime instance
    :return: a string representation of time since `birth_date`.
    """
    if not birth_date:
        return ""
    try:
        return timesince.timesince(birth_date, depth=1)
    except AttributeError:
        return ""


@register.filter
def duration_string(duration, precision="s"):
    """
    Format a duration (e.g. "2 hours, 3 minutes, 35 seconds").
    :param duration: a timedelta instance.
    :param precision: the level of precision to return (h for hours, m for
                      minutes, s for seconds)
    :returns: a string representation of the duration.
    """
    if not duration:
        return ""
    try:
        return utils.duration_string(duration, precision)
    except (ValueError, TypeError):
        return ""


@register.filter
def hours(duration):
    """
    Return the "hours" portion of a duration.
    :param duration: a timedelta instance.
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
    :param duration: a timedelta instance.
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
    :param duration: a timedelta instance.
    :returns: an integer representing the number of seconds in duration.
    """
    if not duration:
        return 0
    try:
        h, m, s = utils.duration_parts(duration)
        return s
    except (ValueError, TypeError):
        return 0


@register.filter()
def dayssince(value, today=None):
    """
    Returns the days since passed datetime in a user friendly way. (e.g. today, yesterday, 2 days ago, ...)
    :param value: a date instance
    :param today: date to compare to (defaults to today)
    :returns: the formatted string
    """

    if today is None:
        today = timezone.localtime().date()

    delta = today - value
    days_ago = _("%(days_ago)s days ago") % {"days_ago": str(delta.days)}

    if delta < datetime.timedelta(days=1):
        return _("today")
    if delta < datetime.timedelta(days=2):
        return _("yesterday")

    # use standard timesince for anything beyond yesterday
    return days_ago


@register.filter
def deltasince(value, now=None):
    """
    Returns a timedelta representing the time since passed datetime
    :param value: a datetime instance
    :param now: datetime to compare to (defaults to now)
    :returns: a timedelta representing the elapsed time
    """
    if now is None:
        now = timezone.now()

    delta = now - value

    return delta
