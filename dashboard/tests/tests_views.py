# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from django.urls import reverse

from faker import Faker

from core.models import Child, Food, Meal


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

        meal = Meal.objects.create(
            child=child,
            time=timezone.now(),
            meal_type="lunch",
            quantity="normal",
        )
        meal.foods.add(Food.objects.get(name="Plátano"))
        page = self.c.get("/children/{}/dashboard/".format(child.slug))
        self.assertContains(page, "Plátano")
        self.assertContains(page, "Meals: 1")
        for route in (
            "core:diaperchange-add",
            "core:medication-add",
            "core:pumping-add",
        ):
            self.assertContains(
                page,
                "{}?child={}".format(reverse(route), child.slug),
            )
        self.assertContains(
            page,
            "{}?child={}".format(reverse("core:feeding-list"), child.pk),
        )
        self.assertContains(page, "btn-dashboard-add-link", count=5)
        self.assertContains(page, "btn-dashboard-sleep", count=1)
        card_order = (
            'data-dashboard-card="feeding-last"',
            'data-dashboard-card="diaper-change-last"',
            'data-dashboard-card="meal-summary"',
            'data-dashboard-card="sleep-last"',
            'data-dashboard-card="medication-last"',
        )
        card_positions = [page.content.find(card.encode()) for card in card_order]
        self.assertNotIn(-1, card_positions)
        self.assertEqual(card_positions, sorted(card_positions))

        Child.objects.create(
            first_name="Second", last_name="Child", birth_date="2000-01-01"
        )
        page = self.c.get("/dashboard/")
        self.assertEqual(page.status_code, 200)
