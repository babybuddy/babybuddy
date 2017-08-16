# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from core.models import Timer


register = template.Library()


@register.inclusion_tag('timer_list.html')
def list_timers(active=True):
    timers = Timer.objects.filter(active=active)
    return {'timers': timers}
