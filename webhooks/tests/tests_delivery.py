# -*- coding: utf-8 -*-
import datetime
import hashlib
import hmac
import json
import threading
from io import StringIO
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from webhooks import delivery
from webhooks.models import WebhookEndpoint, WebhookEvent


class RecordingServerTestCase(TestCase):
    """
    Delivers to a real local server.

    Mocking the HTTP layer would prove that the code calls itself. This proves
    what actually arrives, which is the part a receiving application has to
    cope with.
    """

    def setUp(self):
        call_command("migrate", verbosity=0)
        self.received = []
        self.status = 200
        case = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"])).decode()
                case.received.append(
                    {
                        "path": self.path,
                        "headers": {key: value for key, value in self.headers.items()},
                        "body": body,
                    }
                )
                self.send_response(case.status)
                self.end_headers()
                self.wfile.write(b"thanks")

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.endpoint = WebhookEndpoint.objects.create(
            name="Home",
            url="http://127.0.0.1:{}/hook".format(self.server.server_address[1]),
            secret="the secret of this endpoint",
        )
        self.event = WebhookEvent.objects.create(
            endpoint=self.endpoint,
            type="feeding.created",
            object_id="42",
        )

    def test_what_the_receiver_sees(self):
        delivery.deliver_pending()
        self.assertEqual(len(self.received), 1)
        request = self.received[0]

        self.assertEqual(request["path"], "/hook")
        self.assertEqual(request["headers"]["Content-Type"], "application/json")

        body = json.loads(request["body"])
        self.assertEqual(sorted(body), ["created", "id", "object_id", "type"])
        self.assertEqual(body["type"], "feeding.created")
        self.assertEqual(body["object_id"], "42")
        self.assertEqual(body["id"], str(self.event.event_id))

    def test_nothing_about_the_child_travels(self):
        # The whole point: an endpoint is told that something changed and has
        # to ask the API for the rest, so it can learn nothing from the wire.
        self.event.type = "feeding.created"
        self.event.object_id = "42"
        self.event.save()
        delivery.deliver_pending()
        body = self.received[0]["body"]
        self.assertNotIn("child", body.lower())
        self.assertNotIn("amount", body.lower())
        self.assertNotIn("name", body.lower())

    def test_the_receiver_can_check_the_signature(self):
        delivery.deliver_pending()
        headers = self.received[0]["headers"]
        body = self.received[0]["body"]
        timestamp = headers["X-BabyBuddy-Timestamp"]

        message = "{}.{}".format(timestamp, body).encode()
        expected = hmac.new(
            b"the secret of this endpoint", message, hashlib.sha256
        ).hexdigest()

        self.assertEqual(headers["X-BabyBuddy-Signature"], "v1=" + expected)
        self.assertEqual(headers["X-BabyBuddy-Event-Id"], str(self.event.event_id))
        self.assertEqual(headers["X-BabyBuddy-Event-Type"], "feeding.created")

    def test_each_endpoint_signs_with_its_own_secret(self):
        # Two endpoints on one URL must not be interchangeable: a signature
        # that is good for one has to be worthless for the other.
        other = WebhookEndpoint.objects.create(
            name="Other",
            url=self.endpoint.url,
            secret="a different secret entirely",
        )
        WebhookEvent.objects.create(endpoint=other, type="sleep.created", object_id="7")
        delivery.deliver_pending()
        self.assertEqual(len(self.received), 2)

        secrets_used = set()
        for request in self.received:
            headers = request["headers"]
            timestamp = headers["X-BabyBuddy-Timestamp"]
            message = "{}.{}".format(timestamp, request["body"]).encode()
            for secret in (
                b"the secret of this endpoint",
                b"a different secret entirely",
            ):
                expected = hmac.new(secret, message, hashlib.sha256).hexdigest()
                if headers["X-BabyBuddy-Signature"] == "v1=" + expected:
                    secrets_used.add(secret)
        self.assertEqual(len(secrets_used), 2, "both endpoints used one secret")

    def test_a_tampered_body_is_not_accepted(self):
        delivery.deliver_pending()
        headers = self.received[0]["headers"]
        timestamp = headers["X-BabyBuddy-Timestamp"]

        message = "{}.{}".format(timestamp, "{}").encode()
        expected = hmac.new(
            b"the secret of this endpoint", message, hashlib.sha256
        ).hexdigest()

        self.assertNotEqual(headers["X-BabyBuddy-Signature"], "v1=" + expected)

    def test_the_timestamp_covers_a_replay(self):
        # A captured request cannot be sent again an hour later as it stands:
        # the signature is taken over the timestamp too.
        secret = "the secret of this endpoint"
        first = delivery.signature(secret, 1000, "{}")
        self.assertNotEqual(first, delivery.signature(secret, 1001, "{}"))

    def test_the_command_delivers(self):
        out = StringIO()
        call_command("deliver_webhooks", stdout=out, timeout=5)
        self.assertIn("Delivered 1 event(s).", out.getvalue())
        self.assertEqual(len(self.received), 1)

    def test_the_command_says_so_when_there_is_nothing_to_do(self):
        WebhookEvent.objects.all().delete()
        out = StringIO()
        call_command("deliver_webhooks", stdout=out, timeout=5)
        self.assertIn("Nothing to deliver", out.getvalue())
        self.assertEqual(self.received, [])

    def test_a_delivery_is_recorded(self):
        delivered = delivery.deliver_pending()
        self.assertEqual(delivered, 1)
        self.event.refresh_from_db()
        self.assertIsNotNone(self.event.delivered)
        self.assertEqual(self.event.attempts, 0)
        self.endpoint.refresh_from_db()
        self.assertIsNotNone(self.endpoint.last_delivery)

    def test_a_failed_delivery_is_tried_again_later(self):
        self.status = 500
        now = timezone.now()
        delivery.deliver_pending(now=now)
        self.event.refresh_from_db()
        self.assertIsNone(self.event.delivered)
        self.assertEqual(self.event.attempts, 1)
        self.assertEqual(self.event.last_error, "HTTP 500")
        self.assertEqual(self.event.next_attempt, now + datetime.timedelta(minutes=1))
        # And it goes out again once the wait is over.
        self.status = 200
        delivery.deliver_pending(now=now + datetime.timedelta(minutes=2))
        self.event.refresh_from_db()
        self.assertIsNotNone(self.event.delivered)

    def test_the_waits_double(self):
        self.status = 500
        now = timezone.now()
        for expected_wait, expected_attempts in [(1, 1), (2, 2), (4, 3), (8, 4)]:
            self.event.next_attempt = now
            self.event.save(update_fields=["next_attempt"])
            delivery.deliver_pending(now=now)
            self.event.refresh_from_db()
            self.assertEqual(self.event.attempts, expected_attempts)
            self.assertEqual(
                self.event.next_attempt,
                now + datetime.timedelta(minutes=expected_wait),
            )

    def test_an_event_gives_up_after_the_last_attempt(self):
        self.status = 500
        now = timezone.now()
        for _ in range(delivery.MAX_ATTEMPTS):
            self.event.next_attempt = now
            self.event.save(update_fields=["next_attempt"])
            delivery.deliver_pending(now=now)
            self.event.refresh_from_db()
        self.assertEqual(self.event.attempts, delivery.MAX_ATTEMPTS)
        self.assertIsNone(self.event.next_attempt)

        # Nothing is sent for an event that has given up.
        before = len(self.received)
        delivery.deliver_pending(now=now + datetime.timedelta(days=1))
        self.assertEqual(len(self.received), before)

    def test_a_switched_off_endpoint_is_left_out(self):
        # Turning an endpoint off has to stop it being told things, including
        # what was still queued when the switch went off.
        self.endpoint.active = False
        self.endpoint.save()
        self.assertEqual(delivery.deliver_pending(), 0)
        self.assertEqual(self.received, [])

        # And it goes out when the endpoint is wanted again.
        self.endpoint.active = True
        self.endpoint.save()
        self.assertEqual(delivery.deliver_pending(), 1)
        self.assertEqual(len(self.received), 1)

    def test_an_event_that_is_not_due_is_left_alone(self):
        WebhookEvent.objects.all().update(
            next_attempt=timezone.now() + datetime.timedelta(hours=1)
        )
        self.assertEqual(delivery.deliver_pending(), 0)
        self.assertEqual(self.received, [])

    def test_one_unreachable_endpoint_holds_up_nobody_else(self):
        # This server keeps answering. The second endpoint points at a port
        # nothing is listening on, and must cost only its own events.
        other = WebhookEndpoint.objects.create(
            name="Elsewhere", url="http://127.0.0.1:1/hook", secret="secret"
        )
        WebhookEvent.objects.create(endpoint=other, type="sleep.created", object_id="7")
        now = timezone.now()
        delivered = delivery.deliver_pending(now=now, timeout=1)
        self.assertEqual(delivered, 1)

        self.event.refresh_from_db()
        self.assertIsNotNone(self.event.delivered)

        failed = WebhookEvent.objects.get(endpoint=other)
        self.assertIsNone(failed.delivered)
        self.assertEqual(failed.attempts, 1)
        self.assertTrue(failed.last_error)


class BodyTestCase(TestCase):
    def test_the_body_names_the_change_only(self):
        event = WebhookEvent(
            type="sleep.updated", object_id="abc", created=timezone.now()
        )
        body = json.loads(delivery.body_for(event))
        self.assertEqual(sorted(body), ["created", "id", "object_id", "type"])

    def test_an_event_id_keeps_repeats_apart(self):
        first = WebhookEvent(type="sleep.updated", object_id="abc")
        second = WebhookEvent(type="sleep.updated", object_id="abc")
        self.assertNotEqual(first.event_id, second.event_id)
