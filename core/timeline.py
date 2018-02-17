# -*- coding: utf-8 -*-
from django.utils import timezone

from core.models import DiaperChange, Feeding, Sleep, TummyTime


def get_objects(child, date):
    """
    Create a time-sorted dictionary of all events for a child.
    :param child: an instance of a Child.
    :param date: a DateTime instance for the day to be summarized.
    :returns: a list of the day's events.
    """
    min_date = date
    max_date = date.replace(hour=23, minute=59, second=59)
    events = []

    instances = DiaperChange.objects.filter(child=child).filter(
        time__range=(min_date, max_date)).order_by('-time')
    for instance in instances:
        events.append({
            'time': timezone.localtime(instance.time),
            'event': '{} had a diaper change.'.format(child.first_name),
            'model_name': instance.model_name,
        })

    instances = Feeding.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        events.append({
            'time': timezone.localtime(instance.start),
            'event': '{} started feeding.'.format(instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': '{} finished feeding.'.format(instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'end'
        })

    instances = Sleep.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        events.append({
            'time': timezone.localtime(instance.start),
            'event': '{} fell asleep.'.format(instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': '{} woke up.'.format(instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'end'
        })

    instances = TummyTime.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        events.append({
            'time': timezone.localtime(instance.start),
            'event': '{} started tummy time!'.format(
                instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': '{} finished tummy time.'.format(
                instance.child.first_name),
            'model_name': instance.model_name,
            'type': 'end'
        })

    events.sort(key=lambda x: x['time'], reverse=True)

    return events
