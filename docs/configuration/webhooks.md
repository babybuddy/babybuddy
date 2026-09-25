# Webhooks

_Requires the `deliver_webhooks` command to be run on a schedule._

Webhooks tell another application when something changes in Baby Buddy. Each
endpoint is a URL that receives one request per change, and the receiving
application decides what to do with it.

## What an endpoint receives

The body names the change and carries nothing about its contents:

```json
{
  "created": "2026-09-23T18:04:11.512341+00:00",
  "id": "6f0d1f1e-2d67-4a1e-9a1e-3f9d0c0f0a11",
  "object_id": "42",
  "type": "feeding.created"
}
```

`type` is the record kind and what happened to it, so `feeding.created`,
`feeding.updated` and `feeding.deleted` are all distinct events. `object_id`
identifies the record. Anything that wants the details reads them back through
the [API](../api.md) with its own credentials.

That is all it is told. An endpoint is a URL that somebody configured once and
then left alone, and it is not given the name of a child, how much was fed or
where anyone was. It does see which record kinds changed and when they changed,
which is enough to tell that a household is awake -- so an endpoint is still a
place that knows something about a family, and it is worth treating as one.

## Checking that a request came from Baby Buddy

Every request carries four headers:

| Header                   | Contents                                                                                  |
| ------------------------ | ----------------------------------------------------------------------------------------- |
| `X-BabyBuddy-Event-Id`   | The same value as `id` in the body, for the sake of a receiver that has not parsed it yet |
| `X-BabyBuddy-Event-Type` | The same value as `type` in the body                                                      |
| `X-BabyBuddy-Timestamp`  | The request time, in whole seconds since the epoch                                        |
| `X-BabyBuddy-Signature`  | `v1=` followed by an HMAC-SHA256 hex digest                                               |

The signature covers the timestamp and the body, joined with a period. It does
not cover the headers, so read `id` and `type` out of the body -- that copy is
the one the signature vouches for.

```python
import hashlib
import hmac

received = request.headers["X-BabyBuddy-Signature"].removeprefix("v1=")
timestamp = request.headers["X-BabyBuddy-Timestamp"]
body = request.body  # exactly as it arrived; re-encoding parsed JSON
                     # changes the bytes, and the digest with them

expected = hmac.new(
    secret.encode(),
    timestamp.encode() + b"." + body,
    hashlib.sha256,
).hexdigest()

if not hmac.compare_digest(expected, received):  # not ==, so guessing does not
    raise PermissionError("signature mismatch")  # get easier as it closes in
```

Three things make that check worth something, and two of them are on this side
of the connection:

1. **Check the timestamp** against the current time and refuse anything too far
   off -- a few minutes is usual. Signing the timestamp stops someone _moving_
   it to dress an old body up as a fresh one. It does not stop them sending a
   captured request again exactly as it stands: the digest is the same and it
   verifies forever.
2. **Remember the event ids** you have already acted on, and ignore a repeat.
   Two attempts carry the same `id`, so this also covers a retry.
3. **Compare with `compare_digest`** as above.

Without the first two, a captured request is one that can be used again.

Redirects are not followed. A signature would otherwise end up at whatever host
the endpoint points at next.

## Sending changes

Events are queued as records change and are sent by a command:

```bash
python manage.py deliver_webhooks
```

Run it from cron or a systemd timer. A Docker install has no cron to add to, so
there the command runs from a second container that shares the configuration
and database with the app, on a short loop:

```bash
while true; do python manage.py deliver_webhooks; sleep 30; done
```

Use `https` for anything on another
machine: over plain `http` the secret and the body travel in the clear, and the
signature then proves nothing about where they have been. Anything that is not delivered is tried
again on the next run, waiting twice as long as the previous attempt: one, two,
four and eight minutes. After five attempts the event is left alone and stays
in the database as a record of what happened. An event that is delivered is
removed, so what remains is only what is still waiting or has been given up on.

One endpoint that is down costs only its own events: they are the ones that
fail, and everything else still goes out in the same run. What a slow endpoint
costs is time, since the run works through the list in order and waits up to
ten seconds for each.

## Configuring an endpoint

Endpoints are added under the webhooks section of `/admin/`. Each has a name, a
URL and a secret; the secret is generated when the endpoint is created and can
be replaced at any time. Deactivating an endpoint stops it being told anything, including events
that were still queued when it went off; those wait until it is turned back on.

### From another application

An application can also set up its own endpoint through the [API](../api.md),
at `/api/webhook-endpoints/`, with the same permissions as the admin area: a
user who can add webhook endpoints there can add them here, and caregivers and
read-only users can do neither.

```bash
curl -X POST https://baby.example.com/api/webhook-endpoints/ \
  -H "Authorization: Token <api key>" \
  -H "Content-Type: application/json" \
  -d '{"name": "My phone", "url": "https://receiver.example.com/hook/123"}'
```

The secret is the one field that is never read back. Send `secret` along if the
receiving application issued one — it has to be at least 16 characters — or
leave it out and Baby Buddy generates it and returns it in the response to that
request, the only time it appears. Replacing it later is a `PATCH` with a new
`secret`; switching the endpoint off is a `PATCH` with `"active": false`.

## What is announced

Changes to children and to the entries that can be recorded for them: BMI,
diaper changes, feedings, head circumference, height, medication, notes,
pumping, sleep, temperature, timers, tummy time and weight. Percentiles are
left out because they are computed rather than written, so announcing them
would send an event for every measurement that merely moved a curve.

There is one place where nothing is announced: `QuerySet.update()` writes rows
without calling `save()`, so no signal fires. It is used in migrations and tests
only. A bulk write elsewhere would go unannounced.

An endpoint receives every one of these. `type` is enough to keep what you
want and drop the rest at the receiving end, so there is no filter to configure
here and no way to end up with an endpoint that is quietly not being told about
something you expected it to hear.

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
