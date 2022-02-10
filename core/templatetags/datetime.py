# -*- coding: utf-8 -*-
from django import template
from django.conf import settings
from django.utils import timezone, formats
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag(takes_context=True)
def datetimepicker_format(context, format_string="L LT"):
    """
    Return a datetime format string for momentjs, with support for 24 hour time
    override setting.
    :param context: caller context data
    :param format_string: the default format string (locale based)
    :return: the format string to use, as 24 hour time if configured.
    """
    try:
        user = context["request"].user
        if hasattr(user, "settings") and user.settings.language:
            language = user.settings.language
        else:
            language = settings.LANGUAGE_CODE
    except KeyError:
        language = None

    if settings.USE_24_HOUR_TIME_FORMAT:
        if format_string == "L LT":
            format_string = "L HH:mm"
        elif format_string == "L LTS":
            format_string = "L HH:mm:ss"
    elif language and language == "en-GB":
        # Force 12-hour format if 24 hour format is not configured for en-GB
        # (Django default is 12H, momentjs default is 24H).
        if format_string == "L LT":
            format_string = "L h:mm a"
        elif format_string == "L LTS":
            format_string = "L h:mm:ss a"

    return format_string


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
        datetime_string = _("{}, {}").format(date_string, time_string)
    else:
        datetime_string = date_string

    return datetime_string
