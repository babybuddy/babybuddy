# -*- coding: utf-8 -*-
from django import template
from django.conf import settings
from django.utils import timezone, formats
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter()
def datetime_short(date):
    """
    Format a datetime object as short string for list views
    :param date: datetime instance
    :return: a string representation of `date`.
    """
    date_string = None
    time_string = None

    # The value received from templates will be UTC so it must be converted to
    # localtime here.
    date = timezone.localtime(date)

    now = timezone.localtime()
    if now.date() == date.date():
        date_string = _("Today")
        time_string = formats.date_format(date, format="TIME_FORMAT")
    elif (
        now.year == date.year
        and formats.get_format("SHORT_MONTH_DAY_FORMAT") != "SHORT_MONTH_DAY_FORMAT"
    ):
        # Use the custom `SHORT_MONTH_DAY_FORMAT` format if available for the
        # current locale.
        date_string = formats.date_format(date, format="SHORT_MONTH_DAY_FORMAT")
        time_string = formats.date_format(date, format="TIME_FORMAT")

    if not date_string:
        date_string = formats.date_format(date, format="SHORT_DATETIME_FORMAT")

    if date_string and time_string:
        datetime_string = "{}, {}".format(date_string, time_string)
    else:
        datetime_string = date_string

    return datetime_string
