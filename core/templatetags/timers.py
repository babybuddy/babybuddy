# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import timedelta

from django import template

from core.models import Timer


register = template.Library()


@register.inclusion_tag('core/timer_list.html', takes_context=True)
def list_timers(context, active=True):
    request = context['request'] or None
    timers = Timer.objects.filter(user=request.user, active=active)
    return {'timers': timers}


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


@register.filter
def duration_string(duration):
    if not isinstance(duration, timedelta):
        return duration

    h, remainder = divmod(duration.seconds, 3600)
    m, s = divmod(remainder, 60)

    duration = ''
    if h > 0:
        duration = '{} hour{}'.format(h, 's' if h > 1 else '')
    if m > 0:
        duration += '{}{} minute{}'.format(
            '' if duration is '' else ', ', m, 's' if m > 1 else '')
    if s > 0:
        duration += '{}{} second{}'.format(
            '' if duration is '' else ', ', s, 's' if s > 1 else '')

    return duration


@register.filter
def duration_string_short(duration):
    if not isinstance(duration, timedelta):
        return duration

    h, remainder = divmod(duration.seconds, 3600)
    m, s = divmod(remainder, 60)

    return '{}h {}m {}s'.format(h, m, s)
