# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client as HttpClient, TestCase

from faker import Faker

from core.models import Sleep


class SiteSettingsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(SiteSettingsTestCase, cls).setUpClass()
        fake = Faker()
        call_command("migrate", verbosity=0)
        call_command("fake", verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        cls.credentials = {
            "username": fake_user["username"],
            "password": fake.password(),
        }
        cls.user = get_user_model().objects.create_user(
            is_superuser=True, is_staff=True, **cls.credentials
        )

    def test_settings_default(self):
        self.c.login(**self.credentials)
        page = self.c.get("/settings/")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(
            page.context["form"]["core.models__Sleep__nap_start_max"].value(),
            "18:00:00",
        )
        self.assertEqual(
            page.context["form"]["core.models__Sleep__nap_start_min"].value(),
            "06:00:00",
        )

    def test_settings_nap_start(self):
        self.c.login(**self.credentials)
        params = {
            "core.models__Sleep__nap_start_max": "20:00:00",
            "core.models__Sleep__nap_start_min": "09:00:00",
        }
        page = self.c.post("/settings/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(
            Sleep.settings.nap_start_max.strftime("%H:%M:%S"),
            params["core.models__Sleep__nap_start_max"],
        )
        self.assertEqual(
            Sleep.settings.nap_start_min.strftime("%H:%M:%S"),
            params["core.models__Sleep__nap_start_min"],
        )
