# -*- coding: utf-8 -*-
import secrets
import uuid

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def generate_secret():
    """
    Create the signing secret for a new endpoint.
    :return: a URL-safe random string
    """
    return secrets.token_urlsafe(32)


class WebhookEndpoint(models.Model):
    """
    A URL to notify when a record changes.

    The request names the change and carries none of its contents. An endpoint
    learns which record kind changed and when, and nothing else: not the name
    of a child, not how much was fed, not where anyone was. Anything that wants
    the details reads them back through the API with its own credentials.
    """

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    url = models.URLField(max_length=1000, verbose_name=_("URL"))
    secret = models.CharField(
        default=generate_secret,
        max_length=255,
        verbose_name=_("Secret"),
        help_text=_(
            "Requests are signed with this value. Give it to the receiving "
            "application so it can check that a request came from here."
        ),
    )
    active = models.BooleanField(default=True, verbose_name=_("Active"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created"))
    last_delivery = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Last delivery")
    )

    class Meta:
        ordering = ("name",)
        verbose_name = _("Webhook endpoint")
        verbose_name_plural = _("Webhook endpoints")

    def __str__(self):
        return self.name


class WebhookEvent(models.Model):
    """
    One change, waiting to go to one endpoint.

    The row is written while the change is being saved, and where that save is
    part of a larger transaction the two commit together or not at all. Outside
    one -- a bare ``.save()`` in autocommit -- the entry commits first and the
    events follow, so a process that stops in between keeps the entry and loses
    its announcement. The entry is the important half of that pair: an
    announcement can be missed, a feeding cannot be allowed to vanish.
    """

    endpoint = models.ForeignKey(
        WebhookEndpoint, on_delete=models.CASCADE, related_name="events"
    )
    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name=_("Event ID"),
        help_text=_(
            "Sent with every attempt so the receiving application can discard "
            "a repeat. It is in the body too, and that copy is the one covered "
            "by the signature."
        ),
    )
    type = models.CharField(
        max_length=255,
        verbose_name=_("Type"),
        help_text=_('The kind of change, e.g. "feeding.created".'),
    )
    object_id = models.CharField(max_length=255, verbose_name=_("Object ID"))
    created = models.DateTimeField(auto_now_add=True, verbose_name=_("Created"))
    delivered = models.DateTimeField(blank=True, null=True, verbose_name=_("Delivered"))
    attempts = models.PositiveIntegerField(default=0, verbose_name=_("Attempts"))
    next_attempt = models.DateTimeField(
        default=timezone.now,
        blank=True,
        null=True,
        verbose_name=_("Next attempt"),
        help_text=_(
            "Empty once the attempts are used up: the event stays as a record "
            "and is not tried again."
        ),
    )
    last_error = models.CharField(
        max_length=255, blank=True, verbose_name=_("Last error")
    )

    class Meta:
        ordering = ("-created",)
        verbose_name = _("Webhook event")
        verbose_name_plural = _("Webhook events")

    def __str__(self):
        return "{} {}".format(self.type, self.object_id)
