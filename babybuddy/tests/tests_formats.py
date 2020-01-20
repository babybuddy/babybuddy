# -*- coding: utf-8 -*-
import datetime

from django.core.exceptions import ValidationError
from django.forms.fields import DateTimeField
from django.test import TestCase


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
            result = field.to_python(example)
            self.assertIsInstance(result, datetime.datetime)

        with self.assertRaises(ValidationError):
            field.to_python('invalid date string!')
