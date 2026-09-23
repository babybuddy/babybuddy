# -*- coding: utf-8 -*-
from django.apps import apps
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core import models

from webhooks import signals
from webhooks.models import WebhookEndpoint, WebhookEvent


class WebhookSignalTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.endpoint = WebhookEndpoint.objects.create(
            name="Home", url="http://home.test/hook", secret="secret"
        )
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.event_count = WebhookEvent.objects.count()

    def test_create_is_announced(self):
        models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime(),
            end=timezone.localtime(),
            type="formula",
        )
        event = WebhookEvent.objects.latest("id")
        self.assertEqual(event.type, "feeding.created")
        self.assertEqual(event.object_id, str(models.Feeding.objects.latest("id").pk))
        self.assertEqual(event.endpoint, self.endpoint)
        self.assertIsNone(event.delivered)
        self.assertEqual(WebhookEvent.objects.count(), self.event_count + 1)

    def test_update_is_announced(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime(),
            end=timezone.localtime(),
            type="formula",
        )
        feeding.type = "breast milk"
        feeding.save()
        self.assertEqual(WebhookEvent.objects.latest("id").type, "feeding.updated")

    def test_delete_is_announced(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime(),
            end=timezone.localtime(),
            type="formula",
        )
        primary_key = str(feeding.pk)
        feeding.delete()
        event = WebhookEvent.objects.latest("id")
        self.assertEqual(event.type, "feeding.deleted")
        self.assertEqual(event.object_id, primary_key)

    def test_every_record_model_is_watched(self):
        # A new kind of record is a new kind of change to announce. This fails
        # until it is added on purpose, rather than quietly announcing nothing
        # about it forever.
        from django.db.models import Model

        watched = set(signals.WATCHED)
        for candidate in apps.get_app_config("core").get_models():
            if not issubclass(candidate, Model):
                continue
            if not hasattr(candidate, "model_name"):
                continue
            if "percentile" in candidate.__name__.lower():
                continue
            if candidate in (models.Tag, models.Tagged):
                continue
            self.assertIn(
                candidate,
                watched,
                "{} is not announced by webhooks.signals.WATCHED".format(
                    candidate.__name__
                ),
            )
        self.assertEqual(
            watched,
            set(apps.get_app_config("core").get_models()) & watched,
        )

    def test_a_measurement_announces_the_measurement_only(self):
        # The percentiles are computed rather than written, so a change to a
        # measurement must not announce twice: once for the measurement and
        # once for the curve it moved.
        models.Weight.objects.create(
            child=self.child, date=timezone.localdate(), weight=3.5
        )
        types = set(WebhookEvent.objects.values_list("type", flat=True))
        self.assertIn("weight.created", types)
        self.assertNotIn("weightpercentile.created", types)

    def test_a_bulk_update_is_not_announced(self):
        # The one hole worth naming: `QuerySet.update()` writes rows without
        # calling `save()`, so no signal fires and nothing is announced. It is
        # used in migrations and tests only today. If that ever changes, this
        # test is the reminder that the announcement went with it.
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime(),
            end=timezone.localtime(),
            type="formula",
        )
        before = WebhookEvent.objects.count()
        models.Feeding.objects.filter(pk=feeding.pk).update(type="breast milk")
        self.assertEqual(WebhookEvent.objects.count(), before)

        # A save of the same record still is.
        feeding.refresh_from_db()
        feeding.save()
        self.assertEqual(WebhookEvent.objects.count(), before + 1)

    def test_saving_an_event_is_not_an_event(self):
        WebhookEndpoint.objects.create(
            name="Second", url="http://second.test/hook", secret="secret"
        )
        before = WebhookEvent.objects.count()
        WebhookEvent.objects.create(
            endpoint=self.endpoint, type="feeding.created", object_id="1"
        )
        # Saving an event is not itself an event, or every delivery would queue
        # the next one.
        self.assertEqual(WebhookEvent.objects.count(), before + 1)

    def test_inactive_endpoints_are_skipped(self):
        self.endpoint.active = False
        self.endpoint.save()
        models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime(),
            end=timezone.localtime(),
            type="formula",
        )
        self.assertEqual(WebhookEvent.objects.count(), self.event_count)

    def test_every_active_endpoint_gets_its_own_event(self):
        WebhookEndpoint.objects.create(
            name="Second", url="http://second.test/hook", secret="secret"
        )
        models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime(),
            end=timezone.localtime(),
            type="formula",
        )
        self.assertEqual(WebhookEvent.objects.count(), self.event_count + 2)
        self.assertEqual(
            set(WebhookEvent.objects.values_list("endpoint", flat=True)),
            set(WebhookEndpoint.objects.values_list("id", flat=True)),
        )

    def test_no_endpoints_does_not_break_a_save(self):
        WebhookEvent.objects.all().delete()
        WebhookEndpoint.objects.all().delete()
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime(),
            end=timezone.localtime(),
            type="formula",
        )
        self.assertIsNotNone(feeding.pk)

    def test_a_recording_failure_does_not_break_a_save(self):
        # A webhook is a notification about the entry. If it cannot be queued,
        # the parent must still get the entry.
        original = WebhookEndpoint.objects.filter

        def broken(*args, **kwargs):
            raise RuntimeError("no")

        WebhookEndpoint.objects.filter = broken
        self.addCleanup(setattr, WebhookEndpoint.objects, "filter", original)
        with self.assertLogs("webhooks.signals", level="ERROR"):
            feeding = models.Feeding.objects.create(
                child=self.child,
                start=timezone.localtime(),
                end=timezone.localtime(),
                type="formula",
            )
        self.assertIsNotNone(feeding.pk)
        self.assertEqual(models.Feeding.objects.count(), 1)
