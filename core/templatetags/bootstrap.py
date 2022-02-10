# -*- coding: utf-8 -*-
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def bool_icon(value):
    """
    Create a safe HTML version of True/False using Bootstrap styles.
    :param value: a boolean.
    :returns: a string of html for an icon representing the boolean.
    """
    if value:
        classes = "icon-true text-success"
    else:
        classes = "icon-false text-danger"
    icon_html = '<i class="{}" aria-hidden="true"></i>'.format(classes)
    return mark_safe(icon_html)
