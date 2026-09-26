# -*- coding: utf-8 -*-
"""
Delivery of queued events to their endpoints.

Nothing in here knows what a feeding is. An event names a change and the
receiver decides what to do with it, which is what keeps this service able to
run without any of the log itself.
"""

import datetime
import hashlib
import hmac
import http.client
import json
import logging
import ssl
import time
import urllib.parse

from django.utils import timezone

from webhooks.models import WebhookEvent, WebhookEndpoint

logger = logging.getLogger(__name__)

#: Tries before an event is left alone. Successive tries wait twice as long as
#: the last, so five of them cover about a quarter of an hour.
MAX_ATTEMPTS = 5

#: Seconds to wait for the receiving application before abandoning a try.
TIMEOUT = 10


def signature(secret, timestamp, body):
    """
    The value of the ``X-BabyBuddy-Signature`` header.
    The timestamp is covered along with the body, so the timestamp of a
    captured request cannot be moved to make an old body look fresh. It does
    not stop someone sending a captured request again exactly as it stands --
    the digest is the same and it verifies forever. Rejecting a stale timestamp
    and keeping the event ids already seen is what stops that, and it is the
    receiver that has to do both.
    :param secret: the endpoint's signing secret
    :param timestamp: the request time, in whole seconds since the epoch
    :param body: the request body, as sent
    :return: the hex digest to put behind ``v1=``
    """
    message = "{}.{}".format(timestamp, body).encode()
    return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()


def body_for(event):
    """
    Build the request body for an event.
    Names the change and nothing else: the record itself is read back through
    the API by whoever wants it.
    :param event: a WebhookEvent instance
    :return: the body, as a string
    """
    return json.dumps(
        {
            "id": str(event.event_id),
            "type": event.type,
            "created": event.created.isoformat(),
            "object_id": event.object_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def post(endpoint, event, timeout=TIMEOUT):
    """
    Send one event to one endpoint.

    Redirects are deliberately not followed: a signature would otherwise go out
    to whatever host the endpoint points at next. The signed message covers the
    timestamp and the body only, so the headers are a convenience and the body
    is what a receiver should read.
    :param endpoint: a WebhookEndpoint instance
    :param event: a WebhookEvent instance
    :param timeout: seconds to wait for a response
    :raises ValueError: when the response is not a success
    """
    body = body_for(event)
    timestamp = int(time.time())
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "BabyBuddy",
        "X-BabyBuddy-Event-Id": str(event.event_id),
        "X-BabyBuddy-Event-Type": event.type,
        "X-BabyBuddy-Timestamp": str(timestamp),
        "X-BabyBuddy-Signature": "v1={}".format(
            signature(endpoint.secret, timestamp, body)
        ),
    }
    parts = urllib.parse.urlsplit(endpoint.url)
    if parts.scheme == "https":
        connection = http.client.HTTPSConnection(
            parts.hostname,
            parts.port or 443,
            timeout=timeout,
            context=ssl.create_default_context(),
        )
    elif parts.scheme == "http":
        connection = http.client.HTTPConnection(
            parts.hostname, parts.port or 80, timeout=timeout
        )
    else:
        raise ValueError("Unsupported scheme: {}".format(parts.scheme))
    path = parts.path or "/"
    if parts.query:
        path = "{}?{}".format(path, parts.query)
    try:
        connection.request("POST", path, body=body, headers=headers)
        response = connection.getresponse()
        response.read()
        if not 200 <= response.status < 300:
            raise ValueError("HTTP {}".format(response.status))
    finally:
        connection.close()


def deliver_pending(timeout=TIMEOUT, now=None):
    """
    Send every event that is due.

    One endpoint that is down costs only its own events: each settles on its
    own, and the others are still sent afterwards in the same run. What a slow
    endpoint can cost is time -- the run goes through the list in order and
    waits up to ``timeout`` for each one.

    An endpoint that has been switched off is left out entirely, and what was
    queued for it waits rather than arriving somewhere nobody wants it.

    An event that goes out is removed, so the table holds only what still has
    to be sent or has been given up on and is not read through again.

    :param timeout: seconds to wait for a response
    :param now: the current time, defaulting to the real one
    :return: the number of events delivered
    """
    now = now or timezone.now()
    delivered = 0
    for event in WebhookEvent.objects.filter(
        next_attempt__lte=now, endpoint__active=True
    ).select_related("endpoint"):
        endpoint = event.endpoint
        try:
            post(endpoint, event, timeout=timeout)
        except Exception as error:
            event.attempts += 1
            event.last_error = str(error)[:255]
            if event.attempts >= MAX_ATTEMPTS:
                event.next_attempt = None
            else:
                event.next_attempt = now + datetime.timedelta(
                    minutes=2 ** (event.attempts - 1)
                )
            event.save(update_fields=["attempts", "last_error", "next_attempt"])
            logger.warning(
                "Webhook event %s to %s failed (%s).", event, endpoint.name, error
            )
        else:
            delivered += 1
            endpoint.last_delivery = now
            endpoint.save(update_fields=["last_delivery"])
            event.delete()
    return delivered
