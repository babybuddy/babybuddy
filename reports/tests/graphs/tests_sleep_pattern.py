# -*- coding: utf-8 -*-
import datetime as dt

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs.sleep_pattern import sleep_pattern
from babybuddy.models import Settings


class SleepPatternTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

        self.user = get_user_model().objects.create_user(
            username="sleeppatternuser", password="password"
        )
        self.settings = self.user.settings

    def tearDown(self):
        timezone.activate(self.original_tz)

    def _create_sleep(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()
        models.Sleep.objects.create(
            child=c,
            start=dt.datetime(2000, 1, 1, 0, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2000, 1, 1, 0, 1, tzinfo=dt.timezone.utc),
        )
        return models.Sleep.objects.order_by("start")

    def test_sleep_pattern(self):
        sleep_pattern(self._create_sleep())

    def test_sleep_pattern_tick_labels_12h(self):
        """Y-axis tick labels use 12h format when 24h setting is off."""
        self.settings.hour_format = False
        self.settings.save()

        html, js = sleep_pattern(self._create_sleep())
        self.assertIn("12", js)
        self.assertNotIn('"00:00"', js)

    def test_sleep_pattern_tick_labels_24h(self):
        """Y-axis tick labels use 24h format when 24h setting is on."""
        self.settings.hour_format = True
        self.settings.save()

        html, js = sleep_pattern(self._create_sleep())
        self.assertIn("00:00", js)
        self.assertIn("12:00", js)

    def test_sleep_pattern_label_12h(self):
        """Hover labels do not use bare HH:MM 24h style when 24h is off."""
        self.settings.hour_format = False
        self.settings.save()

        html, js = sleep_pattern(self._create_sleep())
        self.assertNotIn("00:01", js)

    def test_sleep_pattern_label_24h(self):
        """Hover labels use 24h time when 24h setting is on."""
        self.settings.hour_format = True
        self.settings.save()

        html, js = sleep_pattern(self._create_sleep())
        self.assertIn(":", js)
