# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase, override_settings
from django.utils import formats, translation
from django.utils.formats import date_format, get_format


@override_settings(
    FORMAT_MODULE_PATH=["babybuddy.formats_24", "babybuddy.formats"],
)
class Formats24HourTestCase(TestCase):
    """
    The babybuddy.formats_24 module is prepended to FORMAT_MODULE_PATH when
    the USE_24_HOUR_TIME_FORMAT environment variable is truthy, forcing
    24-hour display formats for the English locale family.
    """

    def setUp(self):
        # Django caches loaded format modules per locale; reset so the
        # overridden FORMAT_MODULE_PATH takes effect for this test case.
        formats.reset_format_cache()

    def tearDown(self):
        formats.reset_format_cache()

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

    def test_en_gb_keeps_uk_date_order(self):
        dt = datetime.datetime(year=2021, month=7, day=31, hour=21, minute=5)
        with translation.override("en-gb"):
            self.assertEqual(date_format(dt, "DATE_FORMAT"), "31 Jul 2021")
            self.assertEqual(date_format(dt, "TIME_FORMAT"), "21:05")
            self.assertEqual(date_format(dt, "DATETIME_FORMAT"), "31 Jul 2021, 21:05")
            self.assertEqual(
                date_format(dt, "SHORT_DATETIME_FORMAT"), "31/07/2021 21:05"
            )

    def test_en_gb_keeps_day_first_input_formats(self):
        with translation.override("en-gb"):
            self.assertEqual(
                get_format("DATETIME_INPUT_FORMATS")[3], "%d/%m/%Y %H:%M:%S"
            )
