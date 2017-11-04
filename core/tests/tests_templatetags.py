# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone

from core.templatetags import bootstrap, duration


class TemplateTagsTestCase(TestCase):
    def test_bootstrap_bool_icon(self):
        self.assertEqual(
            bootstrap.bool_icon(True),
            '<i class="icon icon-true text-success" aria-hidden="true"></i>')
        self.assertEqual(
            bootstrap.bool_icon(False),
            '<i class="icon icon-false text-danger" aria-hidden="true"></i>')

    def test_duration_duration_string(self):
        delta = timezone.timedelta(hours=1, minutes=30, seconds=15)
        self.assertEqual(
            duration.duration_string(delta),
            '1 hour, 30 minutes, 15 seconds')
        self.assertEqual(
            duration.duration_string(delta, 'm'),
            '1 hour, 30 minutes')
        self.assertEqual(duration.duration_string(delta, 'h'), '1 hour')

        self.assertEqual(duration.duration_string(''), '')
        self.assertRaises(TypeError, duration.duration_string('not a delta'))

    def test_duration_hours(self):
        delta = timezone.timedelta(hours=1)
        self.assertEqual(duration.hours(delta), 1)
        self.assertEqual(duration.hours(''), 0)
        self.assertRaises(TypeError, duration.hours('not a delta'))

    def test_duration_minutes(self):
        delta = timezone.timedelta(minutes=45)
        self.assertEqual(duration.minutes(delta), 45)
        self.assertEqual(duration.minutes(''), 0)
        self.assertRaises(TypeError, duration.minutes('not a delta'))

    def test_duration_seconds(self):
        delta = timezone.timedelta(seconds=20)
        self.assertEqual(duration.seconds(delta), 20)
        self.assertEqual(duration.seconds(''), 0)
        self.assertRaises(TypeError, duration.seconds('not a delta'))
