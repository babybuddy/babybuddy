# -*- coding: utf-8 -*-
from django import template
from django.db.models import Q, Sum
from django.utils import timezone

from core import models


register = template.Library()


@register.inclusion_tag('cards/diaperchange_last.html')
def card_diaperchange_last(child):
    """
    Information about the most recent diaper change.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Diaper Change instance.
    """
    instance = models.DiaperChange.objects.filter(
        child=child).order_by('-time').first()
    return {'type': 'diaperchange', 'change': instance}


@register.inclusion_tag('cards/diaperchange_types.html')
def card_diaperchange_types(child, date=None):
    """
    Creates a break down of wet and solid Diaper Change instances for the past
    seven days.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dictionary with the wet/dry statistics.
    """
    if not date:
        time = timezone.localtime()
    else:
        time = timezone.datetime.combine(date, timezone.localtime().min.time())
        time = timezone.make_aware(time)
    stats = {}
    week_total = 0
    max_date = (time + timezone.timedelta(days=1)).replace(
        hour=0, minute=0, second=0)
    min_date = (max_date - timezone.timedelta(days=7)).replace(
        hour=0, minute=0, second=0)

    for x in range(7):
        stats[x] = {'wet': 0.0, 'solid': 0.0}

    instances = models.DiaperChange.objects.filter(child=child) \
        .filter(time__gt=min_date).filter(time__lt=max_date).order_by('-time')
    for instance in instances:
        key = (max_date - instance.time).days
        if instance.wet:
            stats[key]['wet'] += 1
        if instance.solid:
            stats[key]['solid'] += 1

    for key, info in stats.items():
        total = info['wet'] + info['solid']
        week_total += total
        if total > 0:
            stats[key]['wet_pct'] = info['wet'] / total * 100
            stats[key]['solid_pct'] = info['solid'] / total * 100

    return {'type': 'diaperchange', 'stats': stats, 'total': week_total}


@register.inclusion_tag('cards/feeding_day.html')
def card_feeding_day(child, date=None):
    """
    Filters Feeding instances to get total amount for a specific date.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dict with count and total amount for the Feeding instances.
    """
    if not date:
        date = timezone.localtime().date()
    instances = models.Feeding.objects.filter(child=child).filter(
        start__year=date.year,
        start__month=date.month,
        start__day=date.day) \
        | models.Feeding.objects.filter(child=child).filter(
        end__year=date.year,
        end__month=date.month,
        end__day=date.day)

    total = sum([instance.amount for instance in instances if instance.amount])
    count = len(instances)

    return {'type': 'feeding', 'total': total, 'count': count}


@register.inclusion_tag('cards/feeding_last.html')
def card_feeding_last(child):
    """
    Information about the most recent feeding.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Feeding instance.
    """
    instance = models.Feeding.objects.filter(child=child) \
        .order_by('-end').first()
    return {'type': 'feeding', 'feeding': instance}


@register.inclusion_tag('cards/feeding_last_method.html')
def card_feeding_last_method(child):
    """
    Information about the three most recent feeding methods.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Feeding instances.
    """
    instances = models.Feeding.objects.filter(child=child) \
        .order_by('-end')[:3]
    # Results are reversed for carousel forward/back behavior.
    return {'type': 'feeding', 'feedings': list(reversed(instances))}


@register.inclusion_tag('cards/sleep_last.html')
def card_sleep_last(child):
    """
    Information about the most recent sleep entry.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Sleep instance.
    """
    instance = models.Sleep.objects.filter(child=child) \
        .order_by('-end').first()
    return {'type': 'sleep', 'sleep': instance}


@register.inclusion_tag('cards/sleep_day.html')
def card_sleep_day(child, date=None):
    """
    Filters Sleep instances to get count and total values for a specific date.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dictionary with count and total values for the Sleep instances.
    """
    if not date:
        date = timezone.localtime().date()
    instances = models.Sleep.objects.filter(child=child).filter(
        start__year=date.year,
        start__month=date.month,
        start__day=date.day) | models.Sleep.objects.filter(child=child).filter(
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

        total += end - start

    count = len(instances)

    return {'type': 'sleep', 'total': total, 'count': count}


@register.inclusion_tag('cards/sleep_naps_day.html')
def card_sleep_naps_day(child, date=None):
    """
    Filters Sleep instances categorized as naps and generates statistics for a
    specific date.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dictionary of nap data statistics.
    """
    if not date:
        date = timezone.localtime().date()
    instances = models.Sleep.naps.filter(child=child).filter(
        start__year=date.year,
        start__month=date.month,
        start__day=date.day) | models.Sleep.naps.filter(child=child).filter(
        end__year=date.year,
        end__month=date.month,
        end__day=date.day)
    return {
        'type': 'sleep',
        'total': instances.aggregate(Sum('duration'))['duration__sum'],
        'count': len(instances)}


@register.inclusion_tag('cards/timer_list.html')
def card_timer_list(child=None):
    """
    Filters for currently active Timer instances, optionally by child.
    :param child: an instance of the Child model.
    :returns: a dictionary with a list of active Timer instances.
    """
    if child:
        # Get active instances for the selected child _or_ None (no child).
        instances = models.Timer.objects.filter(
            Q(active=True),
            Q(child=child) | Q(child=None)
        ).order_by('-start')
    else:
        instances = models.Timer.objects.filter(active=True).order_by('-start')
    return {'type': 'timer', 'instances': list(instances)}


@register.inclusion_tag('cards/tummytime_last.html')
def card_tummytime_last(child):
    """
    Filters the most recent tummy time.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Tummy Time instance.
    """
    instance = models.TummyTime.objects.filter(child=child) \
        .order_by('-end').first()
    return {'type': 'tummytime', 'tummytime': instance}


@register.inclusion_tag('cards/tummytime_day.html')
def card_tummytime_day(child, date=None):
    """
    Filters Tummy Time instances and generates statistics for a specific date.
    :param child: an instance of the Child model.
    :param date: a Date object for the day to filter.
    :returns: a dictionary of all Tummy Time instances and stats for date.
    """
    if not date:
        date = timezone.localtime().date()
    instances = models.TummyTime.objects.filter(
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
