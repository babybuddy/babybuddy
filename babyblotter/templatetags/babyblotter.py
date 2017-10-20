# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template


register = template.Library()


@register.inclusion_tag('babyblotter/breadcrumbs.html', takes_context=True)
def breadcrumbs(context):
    request = context['request'] or None
    # TODO: Process path and send breadcrumbs down.
    return {'path': request.path}
