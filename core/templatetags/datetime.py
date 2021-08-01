# -*- coding: utf-8 -*-
from django import template
from django.conf import settings
from django.utils import timezone, formats
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.simple_tag()
def datetimepicker_format(format_string='L LT'):
    """
    Return a datetime format string for momentjs, with support for 24 hour time
    override setting.
    :param format_string: the default format string (locale based)
    :return: the format string to use, as 24 hour time if configured.
    """
    if settings.USE_24_HOUR_TIME_FORMAT:
        if format_string == 'L LT':
            return 'L HH:mm'
        elif format_string == 'L LTS':
            return 'L HH:mm:ss'
    return format_string


@register.filter()
def datetime_short(date):
    """
    Format a datetime object as short string for list views
    :param date: datetime instance
    :return: a string representation of `date`.
    """
    now = timezone.now()
    time_string = None
    if now.date() == date.date():
        date_string = _('Today')
        time_string = formats.date_format(date, format='TIME_FORMAT')
    elif now.year == date.year:
        date_string = formats.date_format(date, format='SHORT_MONTH_DAY_FORMAT')
        time_string = formats.date_format(date, format='TIME_FORMAT')
    else:
        date_string = formats.date_format(date, format='SHORT_DATETIME_FORMAT')

    if date_string and time_string:
        datetime_string = '{}, {}'.format(date_string, time_string)
    else:
        datetime_string = date_string

    return datetime_string
