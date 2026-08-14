# -*- coding: utf-8 -*-
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from core import models
from core.timeline import get_objects


class TimelineQueryTestCase(TestCase):
    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        now = timezone.localtime()
        self.date = now.replace(hour=12, minute=0, second=0, microsecond=0)

        diaper = models.DiaperChange.objects.create(
            child=self.child, time=self.date, wet=True, solid=False
        )
        diaper.tags.add("wet")
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=self.date,
            end=self.date + timezone.timedelta(minutes=10),
            type="breast milk",
            method="left breast",
        )
        feeding.tags.add("morning")
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=self.date + timezone.timedelta(hours=1),
            end=self.date + timezone.timedelta(hours=2),
            nap=True,
        )
        sleep.tags.add("nap")

    def test_get_objects_returns_events(self):
        events = get_objects(self.date.replace(hour=0, minute=0, second=0), self.child)
        self.assertGreaterEqual(len(events), 3)
        self.assertTrue(any("First" in (event.get("event") or "") for event in events))
        self.assertTrue(any(event.get("tags") for event in events))

    def test_get_objects_query_count_does_not_grow_with_rows(self):
        day = self.date.replace(hour=0, minute=0, second=0, microsecond=0)
        with CaptureQueriesContext(connection) as baseline:
            first = get_objects(day, self.child)
        self.assertGreater(len(first), 0)

        for offset in range(8):
            when = self.date + timezone.timedelta(minutes=offset + 20)
            extra = models.DiaperChange.objects.create(
                child=self.child, time=when, wet=True, solid=False
            )
            extra.tags.add("extra")
            models.Feeding.objects.create(
                child=self.child,
                start=when,
                end=when + timezone.timedelta(minutes=5),
                type="breast milk",
                method="right breast",
            )

        with CaptureQueriesContext(connection) as after:
            second = get_objects(day, self.child)
        self.assertGreater(len(second), len(first))
        self.assertEqual(len(baseline), len(after))
