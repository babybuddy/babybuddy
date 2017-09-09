# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from core.models import Timer


register = template.Library()


@register.inclusion_tag('core/timer_nav.html', takes_context=True)
def timer_nav(context, active=True):
    request = context['request'] or None
    timers = Timer.objects.filter(user=request.user, active=active)
    perms = context['perms'] or None
    # The 'next' parameter is currently not used.
    return {'timers': timers, 'perms': perms, 'next': request.path}


@register.inclusion_tag('core/timer_add.html')
def add_timer(success_url):
    return {'success_url': success_url}
