# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from babybuddy.models import Settings


class SettingsTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)

    def test_settings(self):
        credentials = {"username": "Test", "password": "User"}
        user = get_user_model().objects.create_user(is_superuser=True, **credentials)
        self.assertIsInstance(user.settings, Settings)
        self.assertEqual(user.settings.dashboard_refresh_rate_milliseconds, 60000)

        user.settings.dashboard_refresh_rate = None
        user.save()
        self.assertIsNone(user.settings.dashboard_refresh_rate_milliseconds)

        user.settings.language = "fr"
        user.save()
        self.assertEqual(user.settings.language, "fr")
