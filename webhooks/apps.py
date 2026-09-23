# -*- coding: utf-8 -*-
from django.apps import AppConfig


class WebhooksConfig(AppConfig):
    name = "webhooks"

    def ready(self):
        # Imported for its side effects: the receivers are what turn a change
        # into an event. Anything importing the models alone gets no events.
        from webhooks import signals  # noqa: F401
