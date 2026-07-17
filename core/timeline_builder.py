# -*- coding: utf-8 -*-
from typing import Any

from django.urls import reverse
from django.utils import timezone


class TimelineEventBuilder:
    """
    Build timeline event dictionaries with a consistent structure.
    """

    def __init__(self, instance):
        self._event = {
            "model_name": instance.model_name,
            "tags": instance.tags.all(),
        }
        self._instance = instance

    def with_time(self, value):
        self._event["time"] = timezone.localtime(value)
        return self

    def with_message(self, message):
        self._event["event"] = message
        return self

    def with_details(self, details):
        self._event["details"] = details
        return self

    def with_edit_link(self, route_name):
        self._event["edit_link"] = reverse(
            route_name,
            args=[self._instance.id],
        )
        return self

    def with_type(self, event_type):
        if event_type is not None:
            self._event["type"] = event_type
        return self

    def with_duration(self, duration):
        if duration is not None:
            self._event["duration"] = duration
        return self

    def with_value(self, key: str, value: Any):
        if value is not None:
            self._event[key] = value
        return self

    def build(self):
        return self._event.copy()
