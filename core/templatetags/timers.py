# -*- coding: utf-8 -*-
from django import template

from core.models import Timer


register = template.Library()


@register.inclusion_tag('core/timer_nav.html', takes_context=True)
def timer_nav(context, active=True):
    """
    Get a list of active Timer instances to include in the nav menu.
    :param context: Django's context data.
    :param active: the state of Timers to filter.
    :returns: a dictionary with timers data.
    """
    request = context['request'] or None
    timers = Timer.objects.filter(active=active)
    perms = context['perms'] or None
    # The 'next' parameter is currently not used.
    return {'timers': timers, 'perms': perms, 'next': request.path}
