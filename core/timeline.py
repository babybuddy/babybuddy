# -*- coding: utf-8 -*-
from django.urls import reverse
from django.utils import timezone, timesince
from django.utils.translation import gettext as _

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

    _add_diaper_changes(child, min_date, max_date, events)
    _add_feedings(child, min_date, max_date, events)
    _add_sleeps(child, min_date, max_date, events)
    _add_tummy_times(child, min_date, max_date, events)

    events.sort(key=lambda x: x['time'], reverse=True)

    return events


def _add_tummy_times(child, min_date, max_date, events):
    instances = TummyTime.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        edit_link = reverse('core:tummytime-update', args=[instance.id])
        events.append({
            'time': timezone.localtime(instance.start),
            'event': _('%(child)s started tummy time!') % {
                'child': instance.child.first_name
            },
            'edit_link': edit_link,
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': _('%(child)s finished tummy time.') % {
                'child': instance.child.first_name
            },
            'edit_link': edit_link,
            'duration': timesince.timesince(instance.start, now=instance.end),
            'model_name': instance.model_name,
            'type': 'end'
        })


def _add_sleeps(child, min_date, max_date, events):
    instances = Sleep.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        edit_link = reverse('core:sleep-update', args=[instance.id])
        events.append({
            'time': timezone.localtime(instance.start),
            'event': _('%(child)s fell asleep.') % {
                'child': instance.child.first_name
            },
            'edit_link': edit_link,
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': _('%(child)s woke up.') % {
                'child': instance.child.first_name
            },
            'edit_link': edit_link,
            'duration': timesince.timesince(instance.start, now=instance.end),
            'model_name': instance.model_name,
            'type': 'end'
        })


def _add_feedings(child, min_date, max_date, events):
    instances = Feeding.objects.filter(child=child).filter(
        start__range=(min_date, max_date)).order_by('-start')
    for instance in instances:
        details = None
        edit_link = reverse('core:feeding-update', args=[instance.id])
        if instance.amount:
            details = _('Amount: %(amount).0f') % {
                'amount': instance.amount,
            }
        events.append({
            'time': timezone.localtime(instance.start),
            'event': _('%(child)s started feeding.') % {
                'child': instance.child.first_name
            },
            'details': details,
            'edit_link': edit_link,
            'model_name': instance.model_name,
            'type': 'start'
        })
        events.append({
            'time': timezone.localtime(instance.end),
            'event': _('%(child)s finished feeding.') % {
                'child': instance.child.first_name
            },
            'details': details,
            'edit_link': edit_link,
            'duration': timesince.timesince(instance.start, now=instance.end),
            'model_name': instance.model_name,
            'type': 'end'
        })


def _add_diaper_changes(child, min_date, max_date, events):
    instances = DiaperChange.objects.filter(child=child).filter(
        time__range=(min_date, max_date)).order_by('-time')
    for instance in instances:
        contents = []
        if instance.wet:
            contents.append('💧wet')
        if instance.solid:
            contents.append('💩solid')
        events.append({
            'time': timezone.localtime(instance.time),
            'event': _('%(child)s had a diaper change.') % {
                'child': child.first_name
            },
            'details': _('Contents: %(contents)s') % {
                'contents': ', '.join(contents),
            },
            'edit_link': reverse('core:diaperchange-update',
                                 args=[instance.id]),
            'model_name': instance.model_name
        })
