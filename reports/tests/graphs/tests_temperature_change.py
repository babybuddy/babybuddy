# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs import temperature_change


class TemperatureChangeTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_temperature_change(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()

        models.Temperature.objects.create(
            child=c,
            temperature=98.6,
            time=dt.datetime(2000, 1, 1, 0, 0, tzinfo=dt.timezone.utc),
        )

        html, js = temperature_change(models.Temperature.objects.filter(child=c))
        self.assertIsNotNone(html)
        self.assertIsNotNone(js)
