# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs import tummytime_duration


class TummyTimeDurationTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_tummytime_duration(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()

        models.TummyTime.objects.create(
            child=c,
            start=dt.datetime(2000, 1, 1, 0, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2000, 1, 1, 0, 5, tzinfo=dt.timezone.utc),
        )

        html, js = tummytime_duration(models.TummyTime.objects.filter(child=c))
        self.assertIsNotNone(html)
        self.assertIsNotNone(js)
