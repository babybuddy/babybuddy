# -*- coding: utf-8 -*-
import datetime as dt

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs.feeding_pattern import feeding_pattern
from babybuddy.models import Settings


class FeedingPatternTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

        self.user = get_user_model().objects.create_user(
            username="feedingpatternuser", password="password"
        )
        self.settings = self.user.settings

    def tearDown(self):
        timezone.activate(self.original_tz)

    def _create_feeding(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()
        models.Feeding.objects.create(
            child=c,
            start=dt.datetime(2000, 1, 1, 0, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2000, 1, 1, 0, 1, tzinfo=dt.timezone.utc),
        )
        return models.Feeding.objects.order_by("start")

    def test_feeding_pattern(self):
        feeding_pattern(self._create_feeding())

    def test_feeding_pattern_tick_labels_12h(self):
        """Y-axis tick labels use 12h format when 24h setting is off."""
        self.settings.hour_format = False
        self.settings.save()

        html, js = feeding_pattern(self._create_feeding())
        self.assertIn("12", js)
        self.assertNotIn('"00:00"', js)

    def test_feeding_pattern_tick_labels_24h(self):
        """Y-axis tick labels use 24h format when 24h setting is on."""
        self.settings.hour_format = True
        self.settings.save()

        html, js = feeding_pattern(self._create_feeding())
        self.assertIn("00:00", js)
        self.assertIn("12:00", js)

    def test_feeding_pattern_label_24h(self):
        """Hover labels use 24h time when 24h setting is on."""
        self.settings.hour_format = True
        self.settings.save()

        html, js = feeding_pattern(self._create_feeding())
        self.assertIn(":", js)

    def test_feeding_pattern_label_12h(self):
        """Hover labels do not use bare HH:MM 24h style when 24h is off."""
        self.settings.hour_format = False
        self.settings.save()

        html, js = feeding_pattern(self._create_feeding())
        self.assertNotIn("00:01", js)
