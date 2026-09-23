# -*- coding: utf-8 -*-
import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from core import models as core_models

from webhooks.models import WebhookEndpoint, WebhookEvent

logger = logging.getLogger(__name__)

#: The records worth announcing. Percentiles are left out because they are
#: computed rather than written, and announcing them would send an event for
#: every measurement that merely shifted a curve.
WATCHED = (
    core_models.BMI,
    core_models.Child,
    core_models.DiaperChange,
    core_models.Feeding,
    core_models.HeadCircumference,
    core_models.Height,
    core_models.Medication,
    core_models.Note,
    core_models.Pumping,
    core_models.Sleep,
    core_models.Temperature,
    core_models.Timer,
    core_models.TummyTime,
    core_models.Weight,
)


def record_event(instance, verb):
    """
    Queue one event per active endpoint for a change to ``instance``.

    A failure here is logged and swallowed. This runs inside the transaction
    that saves the entry, so raising would roll back a parent's record over a
    notification about it.
    :param instance: the record that changed
    :param verb: one of "created", "updated" or "deleted"
    """
    event_type = "{}.{}".format(instance._meta.model_name, verb)
    try:
        for endpoint in WebhookEndpoint.objects.filter(active=True):
            WebhookEvent.objects.create(
                endpoint=endpoint,
                type=event_type,
                object_id=str(instance.pk),
            )
    except Exception:
        logger.exception("Could not queue webhook event %s.", event_type)


@receiver(post_save, dispatch_uid="webhooks.record_event_on_save")
def record_event_on_save(sender, instance, created, **kwargs):
    if sender not in WATCHED:
        return
    record_event(instance, "created" if created else "updated")


@receiver(post_delete, dispatch_uid="webhooks.record_event_on_delete")
def record_event_on_delete(sender, instance, **kwargs):
    if sender not in WATCHED:
        return
    record_event(instance, "deleted")
