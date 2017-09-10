# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def bool_icon(value):
    if value:
        classes = 'fa-check-circle-o text-success'
    else:
        classes = 'fa-times-circle-o text-danger'
    icon_html = '<i class="fa {}" aria-hidden="true"></i>'.format(classes)
    return mark_safe(icon_html)
