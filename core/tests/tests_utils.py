# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils import timezone

from core.utils import duration_string, duration_parts


class UtilsTestCase(TestCase):
    def test_duration_string(self):
        duration = timezone.timedelta(hours=1, minutes=30, seconds=45)
        self.assertEqual(
            duration_string(duration),
            '1 hour, 30 minutes, 45 seconds')
        self.assertEqual(duration_string(duration, 'm'), '1 hour, 30 minutes')
        self.assertEqual(duration_string(duration, 'h'), '1 hour')
        self.assertRaises(TypeError, lambda: duration_string('1 hour'))

    def test_duration_parts(self):
        duration = timezone.timedelta(hours=1, minutes=30, seconds=45)
        self.assertEqual(duration_parts(duration), (1, 30, 45))
        self.assertRaises(TypeError, lambda: duration_parts('1 hour'))
