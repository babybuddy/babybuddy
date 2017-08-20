# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict
from datetime import timedelta

from django import template
from django.utils import timezone

from core.models import DiaperChange, Feeding, Sleep, TummyTime


register = template.Library()


@register.inclusion_tag('cards/feeding_last.html')
def card_feeding_last(child):
    instance = Feeding.objects.filter(child=child).order_by('-end').first()
    return {'feeding': instance}


@register.inclusion_tag('cards/diaperchange_last.html')
def card_diaperchange_last(child):
    instance = DiaperChange.objects.filter(
        child=child).order_by('-time').first()
    return {'change': instance}


@register.inclusion_tag('cards/diaperchange_types.html')
def card_diaperchange_types(child):
    """Diaper change statistics for the last five days including today."""
    limit = timezone.now() - timezone.timedelta(days=4)
    instances = DiaperChange.objects.filter(
        child=child).filter(time__gt=limit.date()).order_by('-time')
    stats = OrderedDict()
    for instance in instances:
        date = instance.time.date()
        if date not in stats.keys():
            stats[date] = {'wet': 0, 'solid': 0}
        if instance.wet:
            stats[date]['wet'] += 1
        if instance.solid:
            stats[date]['solid'] += 1

    for date, info in stats.items():
        total = info['wet'] + info['solid']
        stats[date]['wet_pct'] = info['wet'] / total * 100
        stats[date]['solid_pct'] = info['solid'] / total * 100

    return {'stats': stats, 'last_change': instances.last()}


@register.inclusion_tag('cards/tummytime_last.html')
def card_tummytime_last(child):
    instance = TummyTime.objects.filter(child=child).order_by('-end').first()
    return {'tummytime': instance}


@register.inclusion_tag('cards/tummytime_day.html')
def card_tummytime_day(child, date=timezone.now().date()):
    instances = TummyTime.objects.filter(
        child=child, end__day=date.day).order_by('-end')
    stats = {'total': timedelta(seconds=0), 'count': instances.count()}
    for instance in instances:
        stats['total'] += timedelta(seconds=instance.duration_td().seconds)
    return {'stats': stats, 'instances': instances, 'last': instances.first()}


@register.inclusion_tag('cards/sleep_last.html')
def card_sleep_last(child):
    instance = Sleep.objects.filter(child=child).order_by('-end').first()
    return {'sleep': instance}
