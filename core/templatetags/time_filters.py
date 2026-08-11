import datetime

from django import template
from django.template.defaultfilters import time as django_time
from django.utils import timezone
from django.utils.formats import date_format

from babybuddy.models import Settings

register = template.Library()


def _use_24h():
    """Return True if the user-configured hour format is 24-hour."""
    return Settings.objects.filter(hour_format=True).exists()


@register.filter
def hour_format(value):
    """
    Format a time or datetime value using the user's preferred hour format.
    Handles naive/aware datetime objects as well as plain time objects.
    :param value: a datetime or time instance
    :returns: formatted time string
    """
    if value is None:
        return ""

    # If the value is a plain date (not datetime), return empty string –
    # callers wanting date display should use |date or datetime_format.
    if type(value) is datetime.date:
        return ""

    use_24h = _use_24h()

    if isinstance(value, datetime.datetime):
        value = timezone.localtime(value)
        if use_24h:
            return date_format(value, "H:i")
        return django_time(value)
    elif isinstance(value, datetime.time):
        if use_24h:
            return value.strftime("%H:%M")
        return django_time(value)

    return ""


@register.filter
def datetime_format(value):
    """
    Format a date or datetime value for display, respecting the user's
    hour format preference for the time portion.
    Handles both plain date and datetime objects (e.g. Child.birth_datetime).
    :param value: a date or datetime instance
    :returns: formatted date/datetime string
    """
    if value is None:
        return ""

    if isinstance(value, datetime.datetime):
        value = timezone.localtime(value)
        use_24h = _use_24h()
        time_str = date_format(value, "H:i") if use_24h else django_time(value)
        date_str = date_format(value, "DATE_FORMAT")
        return "{} {}".format(date_str, time_str)
    elif isinstance(value, datetime.date):
        return date_format(value, "DATE_FORMAT")

    return str(value)
