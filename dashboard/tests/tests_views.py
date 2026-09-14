# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command
from django.utils import timezone

from faker import Faker

from core.models import Child, Medication, Pumping, TummyTime


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


CARE_ENTRY_PERMISSIONS = (
    "view_child",
    "view_timer",
    "view_feeding",
    "view_diaperchange",
    "view_sleep",
)


class DashboardCardPermissionsTestCase(TestCase):
    """
    Dashboard cards query core models directly, so the child dashboard only
    renders the cards the user has the matching `view` permission for. The
    statistics card combines several models and filters them individually.
    """

    fixtures = ["tests.json"]

    def setUp(self):
        self.child = Child.objects.first()
        now = timezone.localtime()
        Medication.objects.create(
            child=self.child,
            name="Dashboard Test Medication",
            time=now - timezone.timedelta(hours=1),
        )
        Pumping.objects.create(
            child=self.child,
            amount=100,
            start=now - timezone.timedelta(hours=2),
            end=now - timezone.timedelta(hours=2) + timezone.timedelta(minutes=15),
        )
        TummyTime.objects.create(
            child=self.child,
            start=now - timezone.timedelta(hours=3),
            end=now - timezone.timedelta(hours=3) + timezone.timedelta(minutes=5),
        )
        self.c = HttpClient()
        self.url = "/children/{}/dashboard/".format(self.child.slug)

    def _login(self, username, codenames=None, read_only=False):
        user = get_user_model().objects.create_user(
            username=username, password="password", is_active=True
        )
        if read_only:
            # The `read_only` group holds `view` on every core model. The
            # permissions are granted to the user directly, rather than by
            # looking the group up, so this keeps working whether or not the
            # group has been populated.
            codenames = tuple(
                Permission.objects.filter(
                    content_type__app_label="core", codename__startswith="view_"
                ).values_list("codename", flat=True)
            )
        if codenames:
            user.user_permissions.add(
                *Permission.objects.filter(
                    content_type__app_label="core", codename__in=codenames
                )
            )
        self.c.login(username=username, password="password")
        return user

    def test_cards_without_permission_are_not_rendered(self):
        self._login("carer", codenames=CARE_ENTRY_PERMISSIONS)
        page = self.c.get(self.url)
        self.assertEqual(page.status_code, 200)
        content = page.content.decode()

        self.assertNotIn("Dashboard Test Medication", content)
        for heading in ["Last Medication", "Last Pumping", "Today's Tummy Time"]:
            self.assertNotIn(heading, content)

        # The permitted cards are still there.
        self.assertIn("Last Feeding", content)
        self.assertIn("Last Sleep", content)

    def test_statistics_card_excludes_models_without_permission(self):
        self._login("carer", codenames=CARE_ENTRY_PERMISSIONS)
        page = self.c.get(self.url)
        content = page.content.decode()
        for title in [
            "Weight change per week",
            "Height change per week",
            "Head circumference change per week",
            "BMI change per week",
        ]:
            self.assertNotIn(title, content)

    def test_read_only_user_still_sees_every_card(self):
        self._login("readonly", read_only=True)
        page = self.c.get(self.url)
        self.assertEqual(page.status_code, 200)
        content = page.content.decode()
        self.assertIn("Dashboard Test Medication", content)
        self.assertIn("Last Feeding", content)
