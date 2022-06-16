# -*- coding: utf-8 -*-
from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs import sleep_pattern


class SleepPatternTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = ZoneInfo("America/Adak")
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_sleep_pattern(self):

        c = models.Child(birth_date=datetime.now())
        c.save()

        models.Sleep.objects.create(
            child=c,
            start=datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc),
            end=datetime(2000, 1, 1, 0, 1, tzinfo=timezone.utc),
        )

        sleep_pattern(models.Sleep.objects.order_by("start"))
