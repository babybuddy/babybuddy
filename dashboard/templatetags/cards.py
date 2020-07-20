# -*- coding: utf-8 -*-
from django import template
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext as _

from datetime import date, datetime, time

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


@register.inclusion_tag('cards/statistics.html')
def card_statistics(child):
    """
    Statistics data for all models.
    :param child: an instance of the Child model.
    :returns: a list of dictionaries with "type", "stat" and "title" entries.
    """
    stats = []

    changes = _diaperchange_statistics(child)
    stats.append({
        'type': 'duration',
        'stat': changes['btwn_average'],
        'title': _('Diaper change frequency')})

    feedings = _feeding_statistics(child)
    for item in feedings:
        stats.append({
            'type': 'duration',
            'stat': item['btwn_average'],
            'title': item['title']})

    naps = _nap_statistics(child)
    stats.append({
        'type': 'duration',
        'stat': naps['average'],
        'title': _('Average nap duration')})
    stats.append({
        'type': 'float',
        'stat': naps['avg_per_day'],
        'title': _('Average naps per day')})

    sleep = _sleep_statistics(child)
    stats.append({
        'type': 'duration',
        'stat': sleep['average'],
        'title': _('Average sleep duration')})
    stats.append({
        'type': 'duration',
        'stat': sleep['btwn_average'],
        'title': _('Average awake duration')})

    weight = _weight_statistics(child)
    stats.append({
        'type': 'float',
        'stat': weight['change_weekly'],
        'title': _('Weight change per week')})

    return {'stats': stats}


def _diaperchange_statistics(child):
    """
    Averaged Diaper Change data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    instances = models.DiaperChange.objects.filter(child=child) \
        .order_by('time')
    changes = {
        'btwn_total': timezone.timedelta(0),
        'btwn_count': instances.count() - 1,
        'btwn_average': 0.0}
    last_instance = None

    for instance in instances:
        if last_instance:
            changes['btwn_total'] += instance.time - last_instance.time
        last_instance = instance

    if changes['btwn_count'] > 0:
        changes['btwn_average'] = changes['btwn_total'] / changes['btwn_count']

    return changes


def _feeding_statistics(child):
    """
    Averaged Feeding data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    feedings = [
            {
                'start': timezone.now() - timezone.timedelta(days=3),
                'title': _('Feeding frequency (past 3 days)')
            },
            {
                'start': timezone.now() - timezone.timedelta(weeks=2),
                'title': _('Feeding frequency (past 2 weeks)')
            },
            {
                'start': timezone.make_aware(
                    datetime.combine(date.min, time(0, 0))
                    + timezone.timedelta(days=1)),
                'title': _('Feeding frequency')
            }
        ]
    for timespan in feedings:
        timespan['btwn_total'] = timezone.timedelta(0)
        timespan['btwn_count'] = 0
        timespan['btwn_average'] = 0.0

    instances = models.Feeding.objects.filter(child=child).order_by('start')
    last_instance = None

    for instance in instances:
        if last_instance:
            for timespan in feedings:
                if last_instance.start > timespan['start']:
                    timespan['btwn_total'] += (instance.start
                                               - last_instance.end)
                    timespan['btwn_count'] += 1
        last_instance = instance

    for timespan in feedings:
        if timespan['btwn_count'] > 0:
            timespan['btwn_average'] = \
                timespan['btwn_total'] / timespan['btwn_count']
    return feedings


def _nap_statistics(child):
    """
    Averaged nap data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    instances = models.Sleep.naps.filter(child=child).order_by('start')
    naps = {
        'total': instances.aggregate(Sum('duration'))['duration__sum'],
        'count': instances.count(),
        'average': 0.0,
        'avg_per_day': 0.0}
    if naps['count'] > 0:
        naps['average'] = naps['total'] / naps['count']

    naps_avg = instances.annotate(date=TruncDate('start')).values('date') \
        .annotate(naps_count=Count('id')).order_by() \
        .aggregate(Avg('naps_count'))
    naps['avg_per_day'] = naps_avg['naps_count__avg']

    return naps


def _sleep_statistics(child):
    """
    Averaged Sleep data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    instances = models.Sleep.objects.filter(child=child).order_by('start')
    sleep = {
        'total': instances.aggregate(Sum('duration'))['duration__sum'],
        'count': instances.count(),
        'average': 0.0,
        'btwn_total': timezone.timedelta(0),
        'btwn_count': instances.count() - 1,
        'btwn_average': 0.0}

    last_instance = None
    for instance in instances:
        if last_instance:
            sleep['btwn_total'] += instance.start - last_instance.end
        last_instance = instance

    if sleep['count'] > 0:
        sleep['average'] = sleep['total'] / sleep['count']
    if sleep['btwn_count'] > 0:
        sleep['btwn_average'] = sleep['btwn_total'] / sleep['btwn_count']

    return sleep


def _weight_statistics(child):
    """
    Statistical weight data.
    :param child: an instance of the Child model.
    :returns: a dictionary of statistics.
    """
    weight = {'change_weekly': 0.0}

    instances = models.Weight.objects.filter(child=child).order_by('-date')
    newest = instances.first()
    oldest = instances.last()

    if newest != oldest:
        weight_change = newest.weight - oldest.weight
        weeks = (newest.date - oldest.date).days/7
        weight['change_weekly'] = weight_change/weeks

    return weight


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
