# -*- coding: utf-8 -*-
from django.urls import reverse
from django.utils import timezone, timesince
from django.utils.translation import gettext as _

from core.models import DiaperChange, Feeding, Note, Sleep, TummyTime
from datetime import timedelta


def get_objects(date, child=None):
    """
    Create a time-sorted dictionary of all events for a child.
    :param date: a DateTime instance for the day to be summarized.
    :param child: Child instance to filter results for (no filter if `None`).
    :returns: a list of the day's events.
    """
    min_date = date
    max_date = date.replace(hour=23, minute=59, second=59)
    events = []

    _add_diaper_changes(min_date, max_date, events, child)
    _add_feedings(min_date, max_date, events, child)
    _add_sleeps(min_date, max_date, events, child)
    _add_tummy_times(min_date, max_date, events, child)
    _add_notes(min_date, max_date, events, child)

    explicit_type_ordering = {"start": 0, "end": 1}
    events.sort(
        key=lambda x: (
            x["time"],
            explicit_type_ordering.get(x.get("type"), -1),
        ),
        reverse=True,
    )

    return events


def _add_tummy_times(min_date, max_date, events, child=None):
    instances = TummyTime.objects.filter(start__range=(min_date, max_date)).order_by(
        "-start"
    )
    if child:
        instances = instances.filter(child=child)
    for instance in instances:
        details = []
        if instance.milestone:
            details.append(instance.milestone)
        edit_link = reverse("core:tummytime-update", args=[instance.id])
        events.append(
            {
                "time": timezone.localtime(instance.start),
                "event": _("%(child)s started tummy time!")
                % {"child": instance.child.first_name},
                "details": details,
                "edit_link": edit_link,
                "model_name": instance.model_name,
                "type": "start",
            }
        )
        events.append(
            {
                "time": timezone.localtime(instance.end),
                "event": _("%(child)s finished tummy time.")
                % {"child": instance.child.first_name},
                "details": details,
                "edit_link": edit_link,
                "duration": timesince.timesince(instance.start, now=instance.end),
                "model_name": instance.model_name,
                "type": "end",
            }
        )


def _add_sleeps(min_date, max_date, events, child=None):
    instances = Sleep.objects.filter(start__range=(min_date, max_date)).order_by(
        "-start"
    )
    if child:
        instances = instances.filter(child=child)
    for instance in instances:
        details = []
        if instance.notes:
            details.append(instance.notes)
        edit_link = reverse("core:sleep-update", args=[instance.id])
        events.append(
            {
                "time": timezone.localtime(instance.start),
                "event": _("%(child)s fell asleep.")
                % {"child": instance.child.first_name},
                "details": details,
                "edit_link": edit_link,
                "model_name": instance.model_name,
                "type": "start",
            }
        )
        events.append(
            {
                "time": timezone.localtime(instance.end),
                "event": _("%(child)s woke up.") % {"child": instance.child.first_name},
                "details": details,
                "edit_link": edit_link,
                "duration": timesince.timesince(instance.start, now=instance.end),
                "model_name": instance.model_name,
                "type": "end",
            }
        )


def _add_feedings(min_date, max_date, events, child=None):
    # Ensure first feeding has a previous.
    yesterday = min_date - timedelta(days=1)
    prev_start = None

    instances = Feeding.objects.filter(start__range=(yesterday, max_date)).order_by(
        "start"
    )
    if child:
        instances = instances.filter(child=child)
    for instance in instances:
        details = []
        if instance.notes:
            details.append(instance.notes)
        time_since_prev = None
        if prev_start:
            time_since_prev = timesince.timesince(prev_start, now=instance.start)
        prev_start = instance.start
        if instance.start < min_date:
            continue
        edit_link = reverse("core:feeding-update", args=[instance.id])
        if instance.amount:
            details.append(
                _("Amount: %(amount).0f")
                % {
                    "amount": instance.amount,
                }
            )
        events.append(
            {
                "time": timezone.localtime(instance.start),
                "event": _("%(child)s started feeding.")
                % {"child": instance.child.first_name},
                "details": details,
                "edit_link": edit_link,
                "time_since_prev": time_since_prev,
                "model_name": instance.model_name,
                "type": "start",
            }
        )
        events.append(
            {
                "time": timezone.localtime(instance.end),
                "event": _("%(child)s finished feeding.")
                % {"child": instance.child.first_name},
                "details": details,
                "edit_link": edit_link,
                "duration": timesince.timesince(instance.start, now=instance.end),
                "model_name": instance.model_name,
                "type": "end",
            }
        )


def _add_diaper_changes(min_date, max_date, events, child):
    instances = DiaperChange.objects.filter(time__range=(min_date, max_date)).order_by(
        "-time"
    )
    if child:
        instances = instances.filter(child=child)
    for instance in instances:
        contents = []
        if instance.wet:
            contents.append("💧")
        if instance.solid:
            contents.append("💩")
        events.append(
            {
                "time": timezone.localtime(instance.time),
                "event": _("%(child)s had a %(type)s diaper change.")
                % {
                    "child": instance.child.first_name,
                    "type": "".join(contents),
                },
                "edit_link": reverse("core:diaperchange-update", args=[instance.id]),
                "model_name": instance.model_name,
            }
        )


def _add_notes(min_date, max_date, events, child):
    instances = Note.objects.filter(time__range=(min_date, max_date)).order_by("-time")
    if child:
        instances = instances.filter(child=child)
    for instance in instances:
        events.append(
            {
                "time": timezone.localtime(instance.time),
                "details": [instance.note],
                "edit_link": reverse("core:note-update", args=[instance.id]),
                "model_name": instance.model_name,
            }
        )
