# Webhooks

_Requires the `deliver_webhooks` command to be run on a schedule._

Webhooks tell another application when something changes in Baby Buddy. Each
endpoint is a URL that receives one request per change, and the receiving
application decides what to do with it.

## What an endpoint receives

The body names the change and carries nothing about its contents:

```json
{"created":"2026-09-23T18:04:11.512341+00:00","id":"6f0d1f1e-2d67-4a1e-9a1e-3f9d0c0f0a11","object_id":"42","type":"feeding.created"}
```

`type` is the record kind and what happened to it, so `feeding.created`,
`feeding.updated` and `feeding.deleted` are all distinct events. `object_id`
identifies the record. Anything that wants the details reads them back through
the [API](../api.md) with its own credentials.

This is deliberate. An endpoint is a URL that somebody configured once and then
left alone, and it is not told the name of a child, how much was fed or what
time anything happened.

## Checking that a request came from Baby Buddy

Every request carries four headers:

| Header | Contents |
| --- | --- |
| `X-BabyBuddy-Event-Id` | Identifies the change, and is the same on every attempt so a repeat can be discarded |
| `X-BabyBuddy-Event-Type` | The same value as `type` in the body |
| `X-BabyBuddy-Timestamp` | The request time, in whole seconds since the epoch |
| `X-BabyBuddy-Signature` | `v1=` followed by an HMAC-SHA256 hex digest |

The signature is taken over the timestamp and the body, joined with a period:

```python
import hashlib
import hmac

expected = hmac.new(
    secret.encode(),
    f"{timestamp}.{body}".encode(),
    hashlib.sha256,
).hexdigest()

hmac.compare_digest(expected, received_signature)
```

Compare it against what follows `v1=` in `X-BabyBuddy-Signature`, using the
secret from the endpoint's settings. `compare_digest` rather than `==`, so that
guessing a signature does not get easier as it gets closer.

Because the timestamp is covered too, a request that was captured cannot be
sent again later as it stands.

Redirects are not followed. A signature would otherwise end up at whatever host
the endpoint points at next.

## Sending changes

Events are queued as records change and are sent by a command:

```bash
python manage.py deliver_webhooks
```

Run it from cron or a systemd timer. Anything that is not delivered is tried
again on the next run, waiting twice as long as the previous attempt: one, two,
four and eight minutes. After five attempts the event is left alone and stays
in the database as a record of what happened.

One endpoint that is down holds up nobody else. Each event settles on its own,
and a failure costs only the events meant for that endpoint.

## Configuring an endpoint

Endpoints are added under the webhooks section of `/admin/`. Each has a name, a
URL and a secret; the secret is generated when the endpoint is created and can
be replaced at any time. Deactivating an endpoint stops it being told anything, including events
that were still queued when it went off; those wait until it is turned back on.

## What is announced

Changes to children and to the entries that can be recorded for them: BMI,
diaper changes, feedings, head circumference, height, medication, notes,
pumping, sleep, temperature, timers, tummy time and weight. Percentiles are
left out because they are computed rather than written, so announcing them
would send an event for every measurement that merely moved a curve.

There is one place where nothing is announced: `QuerySet.update()` writes rows
without calling `save()`, so no signal fires. It is used in migrations and tests
only. A bulk write elsewhere would go unannounced.

An endpoint receives every one of these. If it only cares about some, it
ignores the rest — the body carries no data worth filtering on, so there is
nothing to filter by either.

## What this does not do

Webhooks are a notification, not a delivery guarantee. Two runs of the command
at the same time can send the same change twice, and the same change goes out
again on every attempt that comes back with a failure. `X-BabyBuddy-Event-Id`
is what tells a repeat from a second change, so keep the ones you have seen if
you cannot afford to act on one twice. Baby Buddy sends one
request per change and gives up after five attempts, and it does not keep a
history of what an endpoint was told. An endpoint that was switched off and on
again has missed whatever happened in between, and the API is what tells it
where things stand now.
