# -*- coding: utf-8 -*-
import logging

from django.db import transaction
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

    Each endpoint is attempted on its own, inside its own savepoint. Two things
    ride on that. One endpoint failing must not cost the others their event,
    and a failure to write an event must leave the caller's transaction usable:
    on a database that aborts a transaction at the first failed statement, an
    unwrapped failure would leave the caller's own save to be rolled back at
    commit time, which is the opposite of what this is for.
    :param instance: the record that changed
    :param verb: one of "created", "updated" or "deleted"
    """
    event_type = "{}.{}".format(instance.model_name, verb)
    # The lookup is guarded as well, in its own savepoint for the same reason:
    # not being able to read the endpoints must not reach the caller any more
    # than failing to write an event does.
    try:
        with transaction.atomic():
            endpoints = list(WebhookEndpoint.objects.filter(active=True))
    except Exception:
        logger.exception("Could not look up webhook endpoints for %s.", event_type)
        return
    for endpoint in endpoints:
        try:
            with transaction.atomic():
                WebhookEvent.objects.create(
                    endpoint=endpoint,
                    type=event_type,
                    object_id=str(instance.pk),
                )
        except Exception:
            logger.exception(
                "Could not queue webhook event %s for %s.", event_type, endpoint.name
            )


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
