# -*- coding: utf-8 -*-
import datetime

from django.core.exceptions import ValidationError
from django.forms.fields import DateTimeField
from django.test import TestCase, override_settings  # , tag
from django.utils.formats import date_format, time_format

from babybuddy.middleware import update_en_gb_date_formats


class GbFormatsTestCase(TestCase):
    @override_settings(LANGUAGE_CODE="en-GB")
    def test_datetime_input_formats(self):
        update_en_gb_date_formats()
        field = DateTimeField()
        supported_custom_examples = [
            "20/01/2020",
            "20/01/2020 9:30 AM",
            "20/01/2020 9:30:03 AM",
            "01/10/2020 11:30 PM",
            "01/10/2020 11:30:03 AM",
        ]

        for example in supported_custom_examples:
            try:
                result = field.to_python(example)
                self.assertIsInstance(result, datetime.datetime)
            except ValidationError:
                self.fail('Format of "{}" not recognized!'.format(example))

        with self.assertRaises(ValidationError):
            field.to_python("invalid date string!")

    # @tag('isolate')
    @override_settings(LANGUAGE_CODE="en-GB", USE_24_HOUR_TIME_FORMAT=True)
    def test_use_24_hour_time_format(self):
        update_en_gb_date_formats()
        field = DateTimeField()
        supported_custom_examples = [
            "25/10/2006 2:30:59",
            "25/10/2006 2:30",
            "25/10/2006 14:30:59",
            "25/10/2006 14:30",
        ]

        for example in supported_custom_examples:
            try:
                result = field.to_python(example)
                self.assertIsInstance(result, datetime.datetime)
            except ValidationError:
                self.fail('Format of "{}" not recognized!'.format(example))

        with self.assertRaises(ValidationError):
            field.to_python("invalid date string!")

        dt = datetime.datetime(year=2011, month=11, day=4, hour=23, minute=5, second=59)
        self.assertEqual(date_format(dt, "DATETIME_FORMAT"), "4 November 2011 23:05:59")

        dt = datetime.datetime(year=2011, month=11, day=4, hour=2, minute=5, second=59)
        self.assertEqual(date_format(dt, "SHORT_DATETIME_FORMAT"), "04/11/2011 02:05")

        t = datetime.time(hour=16, minute=2, second=25)
        self.assertEqual(time_format(t), "16:02")

    # def test_short_month_day_format(self):
    #     update_en_gb_date_formats()
    #     dt = datetime.datetime(year=2021, month=7, day=31, hour=5, minute=5,
    #                            second=5)
    #     self.assertEqual(date_format(dt, 'SHORT_MONTH_DAY_FORMAT'), '31 Jul')
