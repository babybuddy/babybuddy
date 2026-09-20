# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management import call_command

from faker import Faker

from core import models


class ViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(ViewsTestCase, cls).setUpClass()
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
            is_superuser=True, **cls.credentials
        )

        cls.c.login(**cls.credentials)

    def test_graph_child_views(self):
        child = models.Child.objects.first()
        base_url = "/children/{}/reports".format(child.slug)

        page = self.c.get(base_url)
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/bmi/bmi/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/changes/amounts/".format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("{}/changes/lifetimes/".format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("{}/changes/types/".format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("{}/changes/intervals/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/feeding/amounts/".format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("{}/feeding/duration/".format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("{}/feeding/intervals/".format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("{}/feeding/pattern/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/head-circumference/head-circumference/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/height/height/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/pumping/amounts/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/sleep/pattern/".format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("{}/sleep/totals/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/temperature/temperature/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/tummy-time/duration/".format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("{}/weight/weight/".format(base_url))
        self.assertEqual(page.status_code, 200)


CARE_ENTRY_PERMISSIONS = (
    "view_child",
    "view_timer",
    "view_feeding",
    "view_diaperchange",
    "view_sleep",
)


class ReportPermissionsTestCase(TestCase):
    """
    Every report renders entries from one model, so opening it requires the
    `view` permission for that model on top of `core.view_child`. Without this
    a user who may only see feedings could read the growth and medication
    reports.
    """

    fixtures = ["tests.json"]

    allowed = [
        "/changes/amounts/",
        "/changes/intervals/",
        "/changes/lifetimes/",
        "/changes/types/",
        "/feeding/amounts/",
        "/feeding/duration/",
        "/feeding/intervals/",
        "/feeding/pattern/",
        "/sleep/pattern/",
        "/sleep/totals/",
    ]
    denied = [
        "/bmi/bmi/",
        "/head-circumference/head-circumference/",
        "/height/height/",
        "/height/boy/",
        "/height/girl/",
        "/medication/frequency/",
        "/medication/intervals/",
        "/pumping/amounts/",
        "/temperature/temperature/",
        "/tummy-time/duration/",
        "/weight/weight/",
        "/weight/boy/",
        "/weight/girl/",
    ]

    def setUp(self):
        self.child = models.Child.objects.first()
        self.base_url = "/children/{}/reports".format(self.child.slug)
        self.c = HttpClient()

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

    def test_care_entry_permissions_open_matching_reports(self):
        self._login("carer", codenames=CARE_ENTRY_PERMISSIONS)
        for path in self.allowed:
            page = self.c.get("{}{}".format(self.base_url, path))
            self.assertEqual(page.status_code, 200, path)

    def test_care_entry_permissions_do_not_open_other_reports(self):
        self._login("carer", codenames=CARE_ENTRY_PERMISSIONS)
        for path in self.denied:
            page = self.c.get("{}{}".format(self.base_url, path))
            self.assertEqual(page.status_code, 403, path)

    def test_report_list_only_offers_permitted_reports(self):
        self._login("carer", codenames=CARE_ENTRY_PERMISSIONS)
        page = self.c.get(self.base_url)
        self.assertEqual(page.status_code, 200)
        content = page.content.decode()
        for path in self.allowed:
            self.assertIn("{}{}".format(self.base_url, path), content, path)
        for path in self.denied:
            self.assertNotIn("{}{}".format(self.base_url, path), content, path)

    def test_read_only_user_keeps_access_to_every_report(self):
        self._login("readonly", read_only=True)
        for path in self.allowed + self.denied:
            page = self.c.get("{}{}".format(self.base_url, path))
            self.assertEqual(page.status_code, 200, path)
