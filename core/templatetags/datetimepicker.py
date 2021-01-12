# -*- coding: utf-8 -*-
from django import template
from django.conf import settings

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
