# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from django.utils.formats import date_format


class FormatsTestCase(TestCase):
    def test_short_month_day_format(self):
        dt = datetime.datetime(year=2021, month=7, day=31, hour=5, minute=5, second=5)
        self.assertEqual(date_format(dt, "SHORT_MONTH_DAY_FORMAT"), "Jul 31")
