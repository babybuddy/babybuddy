# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase, override_settings
from django.utils import formats
from django.utils.formats import date_format, get_format


@override_settings(
    FORMAT_MODULE_PATH=["babybuddy.formats_24", "babybuddy.formats"],
)
class Formats24HourTestCase(TestCase):
    """
    The babybuddy.formats_24 module is prepended to FORMAT_MODULE_PATH when
    the USE_24_HOUR_TIME_FORMAT environment variable is truthy, forcing
    24-hour display and input formats for the English locale family.
    """

    def setUp(self):
        # Django caches loaded format modules per locale; reset so the
        # overridden FORMAT_MODULE_PATH takes effect for this test case.
        formats._format_cache.clear()
        formats._format_modules_cache.clear()

    def tearDown(self):
        formats._format_cache.clear()
        formats._format_modules_cache.clear()

    def test_time_format_is_24_hour(self):
        dt = datetime.datetime(year=2021, month=7, day=31, hour=21, minute=5)
        self.assertEqual(date_format(dt, "TIME_FORMAT"), "21:05")

    def test_short_datetime_format_is_24_hour(self):
        dt = datetime.datetime(year=2021, month=7, day=31, hour=21, minute=5)
        self.assertEqual(date_format(dt, "SHORT_DATETIME_FORMAT"), "07/31/2021 21:05")

    def test_short_month_day_format_preserved(self):
        # The customization from babybuddy.formats.en must survive the
        # override module being prepended.
        dt = datetime.datetime(year=2021, month=7, day=31, hour=5, minute=5)
        self.assertEqual(date_format(dt, "SHORT_MONTH_DAY_FORMAT"), "Jul 31")

    def test_time_input_formats_accept_24_hour(self):
        self.assertIn("%H:%M", get_format("TIME_INPUT_FORMATS"))
