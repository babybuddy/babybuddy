# -*- coding: utf-8 -*-
from datetime import timedelta
from typing import Callable

from django.utils.translation import gettext as _

from core.models import Sleep
from core.timeline_builder import TimelineEventBuilder


class SleepTimelineStrategy:
    """
    Generate timeline events for sleep records.
    """

    def __init__(self, duration_formatter: Callable):
        self._duration_formatter = duration_formatter

    def add_events(self, min_date, max_date, events, child=None):
        instances = Sleep.objects.filter(start__range=(min_date, max_date)).order_by(
            "-start"
        )

        if child:
            instances = instances.filter(child=child)

        for instance in instances:
            details = []
            if instance.notes:
                details.append(instance.notes)

            start_event = (
                TimelineEventBuilder(instance)
                .with_time(instance.start)
                .with_message(
                    _("%(child)s fell asleep.") % {"child": instance.child.first_name}
                )
                .with_details(details)
                .with_edit_link("core:sleep-update")
                .with_type("start")
                .build()
            )
            events.append(start_event)

            end_builder = (
                TimelineEventBuilder(instance)
                .with_time(instance.end)
                .with_message(
                    _("%(child)s woke up.") % {"child": instance.child.first_name}
                )
                .with_details(details)
                .with_edit_link("core:sleep-update")
                .with_type("end")
            )

            if instance.duration > timedelta(seconds=0):
                end_builder.with_duration(self._duration_formatter(instance.duration))

            events.append(end_builder.build())
