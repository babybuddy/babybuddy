# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs import diaperchange_lifetimes


class DiaperChangeLifetimesTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_diaperchange_lifetimes(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()

        models.DiaperChange.objects.create(
            child=c,
            time=dt.datetime(2000, 1, 1, 0, 0, tzinfo=dt.timezone.utc),
            wet=True,
            solid=False,
        )
        models.DiaperChange.objects.create(
            child=c,
            time=dt.datetime(2000, 1, 1, 4, 0, tzinfo=dt.timezone.utc),
            wet=False,
            solid=True,
        )

        html, js = diaperchange_lifetimes(
            models.DiaperChange.objects.filter(child=c).order_by("time")
        )
        self.assertIsNotNone(html)
        self.assertIsNotNone(js)
