# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def bool_icon(value):
    if value:
        classes = 'icon-true text-success'
    else:
        classes = 'icon-false text-danger'
    icon_html = '<i class="icon {}" aria-hidden="true"></i>'.format(classes)
    return mark_safe(icon_html)
