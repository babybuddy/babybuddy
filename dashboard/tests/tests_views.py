# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth import get_user_model
from django.core.management import call_command

from faker import Faker

from core.models import Child


class ViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(ViewsTestCase, cls).setUpClass()
        fake = Faker()
        call_command("migrate", verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        cls.credentials = {
            "username": fake_user["username"],
            "password": fake.password(),
        }
        cls.user = get_user_model().objects.create_user(
            is_superuser=True, **cls.credentials
        )

        cls.c.login(**cls.credentials)

    def test_dashboard_views(self):
        page = self.c.get("/dashboard/")
        self.assertEqual(page.url, "/welcome/")

        call_command("fake", verbosity=0, children=1, days=1)
        child = Child.objects.first()
        page = self.c.get("/dashboard/")
        self.assertEqual(page.url, "/children/{}/dashboard/".format(child.slug))

        page = self.c.get("/dashboard/")
        self.assertEqual(page.url, "/children/{}/dashboard/".format(child.slug))
        # Test the actual child dashboard (including cards).
        # TODO: Test cards more granularly.
        page = self.c.get("/children/{}/dashboard/".format(child.slug))
        self.assertEqual(page.status_code, 200)

        Child.objects.create(
            first_name="Second", last_name="Child", birth_date="2000-01-01"
        )
        page = self.c.get("/dashboard/")
        self.assertEqual(page.status_code, 200)

    def test_customize_cards_page(self):
        """The combined customize page should return 200."""
        call_command("fake", verbosity=0, children=1, days=1)
        page = self.c.get("/dashboard/cards/")
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Customize Dashboard")
        # Should contain the breast_activity_time_mode toggle
        self.assertContains(page, "breast_activity_time_mode")
        self.assertContains(page, "Start time")

    def test_reorder_redirects_to_cards(self):
        """The old reorder URL should redirect to the combined page."""
        call_command("fake", verbosity=0, children=1, days=1)
        page = self.c.get("/dashboard/reorder/")
        self.assertEqual(page.status_code, 302)
        self.assertEqual(page.url, "/dashboard/cards/")

    def test_customize_cards_post_saves_visibility_and_order(self):
        """POST to customize page should save both visibility and order."""
        call_command("fake", verbosity=0, children=1, days=1)
        # Toggle some cards, set an order
        response = self.c.post("/dashboard/cards/", {
            "card_timer_list": "on",
            "card_feeding_last": "on",
            "card_breast_activity": "on",
            "card_order": ["breast_activity", "feeding_last", "timer_list"],
            "breast_activity_time_mode": "start",
        })
        self.assertEqual(response.status_code, 302)
        # Verify saved
        from babybuddy.models import Settings
        settings = Settings.objects.get(user=self.user)
        config = settings.dashboard_card_config
        self.assertEqual(config["_card_order"], ["breast_activity", "feeding_last", "timer_list"])
        self.assertEqual(settings.breast_activity_time_mode, "start")
        # Hidden card should be saved as not visible
        self.assertFalse(config.get("sleep_last", {}).get("visible", True))

    def test_customize_cards_post_breast_mode_end(self):
        """POST with end mode should save correctly."""
        call_command("fake", verbosity=0, children=1, days=1)
        response = self.c.post("/dashboard/cards/", {
            "card_timer_list": "on",
            "card_order": ["timer_list"],
            "breast_activity_time_mode": "end",
        })
        self.assertEqual(response.status_code, 302)
        from babybuddy.models import Settings
        settings = Settings.objects.get(user=self.user)
        self.assertEqual(settings.breast_activity_time_mode, "end")

    def test_customize_cards_invalid_breast_mode_defaults_to_end(self):
        """Invalid mode value should not corrupt the setting."""
        call_command("fake", verbosity=0, children=1, days=1)
        # Set to a valid value first
        from babybuddy.models import Settings
        settings = Settings.objects.get(user=self.user)
        settings.breast_activity_time_mode = "end"
        settings.save()
        # POST with invalid value (should be ignored, keep "end")
        response = self.c.post("/dashboard/cards/", {
            "card_timer_list": "on",
            "card_order": ["timer_list"],
            "breast_activity_time_mode": "invalid",
        })
        self.assertEqual(response.status_code, 302)
        settings.refresh_from_db()
        self.assertEqual(settings.breast_activity_time_mode, "end")
