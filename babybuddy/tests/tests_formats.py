# -*- coding: utf-8 -*-
import datetime

from django.core.exceptions import ValidationError
from django.forms.fields import DateTimeField
from django.test import TestCase, override_settings, tag
from django.utils.formats import date_format, time_format


class FormatsTestCase(TestCase):
    def test_datetime_input_formats(self):
        field = DateTimeField()
        supported_custom_examples = [
            '01/20/2020 9:30 AM',
            '01/20/2020 9:30:03 AM',
            '10/01/2020 11:30 PM',
            '10/01/2020 11:30:03 AM',
        ]

        for example in supported_custom_examples:
            try:
                result = field.to_python(example)
                self.assertIsInstance(result, datetime.datetime)
            except ValidationError:
                self.fail('Format of "{}" not recognized!'.format(example))

        with self.assertRaises(ValidationError):
            field.to_python('invalid date string!')

    @tag('isolate')
    @override_settings(LANGUAGE_CODE='en', USE_24_HOUR_TIME_FORMAT=True)
    def test_use_24_hour_time_format_en(self):
        field = DateTimeField()
        supported_custom_examples = [
            '10/25/2006 2:30:59',
            '10/25/2006 2:30',
            '10/25/2006 14:30:59',
            '10/25/2006 14:30',
        ]

        for example in supported_custom_examples:
            try:
                result = field.to_python(example)
                self.assertIsInstance(result, datetime.datetime)
            except ValidationError:
                self.fail('Format of "{}" not recognized!'.format(example))

        with self.assertRaises(ValidationError):
            field.to_python('invalid date string!')

        dt = datetime.datetime(year=2011, month=11, day=4, hour=23, minute=5,
                               second=59)
        self.assertEqual(
            date_format(dt, 'DATETIME_FORMAT'), 'Nov. 4, 2011, 23:05:59')

        dt = datetime.datetime(year=2011, month=11, day=4, hour=2, minute=5,
                               second=59)
        self.assertEqual(
            date_format(dt, 'SHORT_DATETIME_FORMAT'), '11/04/2011 2:05:59')

        t = datetime.time(hour=16, minute=2, second=25)
        self.assertEqual(time_format(t), '16:02:25')
