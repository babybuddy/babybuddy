# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils import timezone

from core import utils


class UtilsTestCase(TestCase):
    def test_duration_string(self):
        duration = timezone.timedelta(hours=1, minutes=30, seconds=45)
        self.assertEqual(
            utils.duration_string(duration), "1 hour, 30 minutes, 45 seconds"
        )
        self.assertEqual(utils.duration_string(duration, "m"), "1 hour, 30 minutes")
        self.assertEqual(utils.duration_string(duration, "h"), "1 hour")
        self.assertRaises(TypeError, lambda: utils.duration_string("1 hour"))

    def test_duration_parts(self):
        duration = timezone.timedelta(hours=1, minutes=30, seconds=45)
        self.assertEqual(utils.duration_parts(duration), (1, 30, 45))
        self.assertRaises(TypeError, lambda: utils.duration_parts("1 hour"))

    def test_random_color(self):
        color = utils.random_color()
        self.assertIsInstance(color, str)
        self.assertIn(color, utils.COLORS)
