# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs import bmi_change


class BMIChangeTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_bmi_change(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()

        models.BMI.objects.create(
            child=c,
            bmi=18.5,
            date=dt.date(2000, 1, 1),
        )

        html, js = bmi_change(models.BMI.objects.filter(child=c))
        self.assertIsNotNone(html)
        self.assertIsNotNone(js)
