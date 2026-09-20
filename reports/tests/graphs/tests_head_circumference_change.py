# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs import head_circumference_change


class HeadCircumferenceChangeTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_head_circumference_change(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()

        models.HeadCircumference.objects.create(
            child=c,
            head_circumference=35.0,
            date=dt.date(2000, 1, 1),
        )

        html, js = head_circumference_change(
            models.HeadCircumference.objects.filter(child=c)
        )
        self.assertIsNotNone(html)
        self.assertIsNotNone(js)
