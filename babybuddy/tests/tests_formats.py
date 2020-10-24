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
