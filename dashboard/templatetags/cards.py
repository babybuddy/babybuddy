# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.db.models import Sum
from django.utils import timezone

from core.models import DiaperChange, Feeding, Sleep, Timer, TummyTime


register = template.Library()


@register.inclusion_tag('cards/averages.html')
def card_averages(child):
    """Averages data for all models.
    """
    instances = Sleep.objects.filter(child=child).order_by('start')
    sleep = {
        'total': instances.aggregate(Sum('duration'))['duration__sum'],
        'count': instances.count(),
        'average': 0,
        'btwn_total': timezone.timedelta(0),
        'btwn_count': instances.count() - 1,
        'btwn_average': 0}

    last_instance = None
    for instance in instances:
        if last_instance:
            sleep['btwn_total'] += instance.start - last_instance.end
        last_instance = instance

    if sleep['count'] > 0:
        sleep['average'] = sleep['total']/sleep['count']
    if sleep['btwn_count'] > 0:
        sleep['btwn_average'] = sleep['btwn_total']/sleep['btwn_count']

    instances = DiaperChange.objects.filter(child=child).order_by('time')
    changes = {
        'btwn_total': timezone.timedelta(0),
        'btwn_count': instances.count() - 1,
        'btwn_average': 0}
    last_instance = None

    for instance in instances:
        if last_instance:
            changes['btwn_total'] += instance.time - last_instance.time
        last_instance = instance

    if changes['btwn_count'] > 0:
        changes['btwn_average'] = changes['btwn_total']/changes['btwn_count']

    instances = Feeding.objects.filter(child=child).order_by('start')
    feedings = {
        'btwn_total': timezone.timedelta(0),
        'btwn_count': instances.count() - 1,
        'btwn_average': 0}
    last_instance = None

    for instance in instances:
        if last_instance:
            feedings['btwn_total'] += instance.start - last_instance.end
        last_instance = instance

    if feedings['btwn_count'] > 0:
        feedings['btwn_average'] = \
            feedings['btwn_total']/feedings['btwn_count']

    return {'changes': changes, 'feedings': feedings, 'sleep': sleep}


@register.inclusion_tag('cards/diaperchange_last.html')
def card_diaperchange_last(child):
    """Information about the most recent diaper change.
    """
    instance = DiaperChange.objects.filter(
        child=child).order_by('-time').first()
    return {'type': 'diaperchange', 'change': instance}


@register.inclusion_tag('cards/diaperchange_types.html')
def card_diaperchange_types(child):
    """Diaper change statistics for the last seven days including today.
    """
    stats = {}
    max_date = (timezone.localtime() + timezone.timedelta(
        days=1)).replace(hour=0, minute=0, second=0)
    min_date = (max_date - timezone.timedelta(
        days=6)).replace(hour=0, minute=0, second=0)

    for x in range(6):
        stats[x] = {'wet': 0, 'solid': 0}

    instances = DiaperChange.objects.filter(child=child) \
        .filter(time__gt=min_date).filter(time__lt=max_date).order_by('-time')
    for instance in instances:
        key = (max_date - instance.time).days
        if instance.wet:
            stats[key]['wet'] += 1
        if instance.solid:
            stats[key]['solid'] += 1

    for key, info in stats.items():
        total = info['wet'] + info['solid']
        if total > 0:
            stats[key]['wet_pct'] = info['wet'] / total * 100
            stats[key]['solid_pct'] = info['solid'] / total * 100

    return {
        'type': 'diaperchange',
        'stats': stats,
        'last_change': instances.first()}


@register.inclusion_tag('cards/feeding_last.html')
def card_feeding_last(child):
    """Information about the most recent feeding.
    """
    instance = Feeding.objects.filter(child=child).order_by('-end').first()
    return {'type': 'feeding', 'feeding': instance}


@register.inclusion_tag('cards/feeding_last_method.html')
def card_feeding_last_method(child):
    """Information about the most recent feeding _method_.
    """
    instance = Feeding.objects.filter(child=child).order_by('-end').first()
    return {'type': 'feeding', 'feeding': instance}


@register.inclusion_tag('cards/sleep_last.html')
def card_sleep_last(child):
    """Information about the most recent sleep entry.
    """
    instance = Sleep.objects.filter(child=child).order_by('-end').first()
    return {'type': 'sleep', 'sleep': instance}


@register.inclusion_tag('cards/sleep_day.html')
def card_sleep_day(child, date=None):
    """Total sleep time for a child on the current day.
    """
    if not date:
        date = timezone.localtime().date()
    instances = Sleep.objects.filter(child=child).filter(
        start__year=date.year,
        start__month=date.month,
        start__day=date.day) | Sleep.objects.filter(child=child).filter(
        end__year=date.year,
        end__month=date.month,
        end__day=date.day)

    total = timezone.timedelta(seconds=0)
    for instance in instances:
        start = timezone.localtime(instance.start)
        end = timezone.localtime(instance.end)
        # Account for dates crossing midnight.
        if start.date() != date:
            start = start.replace(year=end.year, month=end.month, day=end.day,
                                  hour=0, minute=0, second=0)
        elif end.date() != date:
            end = start.replace(year=start.year, month=start.month,
                                day=start.day, hour=23, minute=59, second=59)

        total += end - start

    count = len(instances)

    return {'type': 'sleep', 'total': total, 'count': count}


@register.inclusion_tag('cards/sleep_naps_day.html')
def card_sleep_naps_day(child, date=None):
    """Nap information for the current day.
    """
    local = timezone.localtime(date)
    start_lower = local.replace(
        hour=7, minute=0, second=0).astimezone(timezone.utc)
    start_upper = local.replace(
        hour=19, minute=0, second=0).astimezone(timezone.utc)
    instances = Sleep.objects.filter(child=child) \
        .filter(start__gte=start_lower, start__lte=start_upper)
    return {
        'type': 'sleep',
        'total': instances.aggregate(Sum('duration')),
        'count': len(instances)}


@register.inclusion_tag('cards/timer_list.html')
def card_timer_list():
    """Information about currently active timers.
    """
    instances = Timer.objects.filter(active=True).order_by('-start')
    return {'type': 'timer', 'instances': list(instances)}


@register.inclusion_tag('cards/tummytime_last.html')
def card_tummytime_last(child):
    """Information about the most recent tummy time.
    """
    instance = TummyTime.objects.filter(child=child).order_by('-end').first()
    return {'type': 'tummytime', 'tummytime': instance}


@register.inclusion_tag('cards/tummytime_day.html')
def card_tummytime_day(child, date=None):
    """Tummy time over the course of `date`.
    """
    if not date:
        date = timezone.localtime().date()
    instances = TummyTime.objects.filter(
        child=child, end__year=date.year, end__month=date.month,
        end__day=date.day).order_by('-end')
    stats = {
        'total': timezone.timedelta(seconds=0),
        'count': instances.count()
    }
    for instance in instances:
        stats['total'] += timezone.timedelta(seconds=instance.duration.seconds)
    return {
        'type': 'tummytime',
        'stats': stats,
        'instances': instances,
        'last': instances.first()}
