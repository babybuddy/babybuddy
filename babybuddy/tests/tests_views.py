# -*- coding: utf-8 -*-
import re
import time

from django.test import TestCase, override_settings, tag
from django.test import Client as HttpClient
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command

from faker import Faker

from babybuddy.views import UserUnlock


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
            is_superuser=True, email="admin@admin.admin", **cls.credentials
        )

        cls.c.login(**cls.credentials)

    def test_root_router(self):
        page = self.c.get("/")
        self.assertEqual(page.url, "/dashboard/")

    @override_settings(ROLLING_SESSION_REFRESH=1)
    def test_rolling_sessions(self):
        self.c.get("/")
        session1 = str(self.c.cookies["sessionid"])
        # Sleep longer than ROLLING_SESSION_REFRESH.
        time.sleep(2)
        self.c.get("/")
        session2 = str(self.c.cookies["sessionid"])
        self.c.get("/")
        session3 = str(self.c.cookies["sessionid"])
        self.assertNotEqual(session1, session2)
        self.assertEqual(session2, session3)

    def test_user_settings(self):
        page = self.c.get("/user/settings/")
        self.assertEqual(page.status_code, 200)

    def test_add_device_page(self):
        page = self.c.get("/user/add-device/")
        self.assertRegex(
            page.content.decode(),
            r""".*<div [^>]* data-qr-code-content="[^"]+"[^>]*>.*""",
        )

    def test_user_views(self):
        # Staff setting is required to access user management.
        page = self.c.get("/users/")
        self.assertEqual(page.status_code, 403)
        self.user.is_staff = True
        self.user.save()

        page = self.c.get("/users/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/users/add/")
        self.assertEqual(page.status_code, 200)

        entry = get_user_model().objects.first()
        page = self.c.get("/users/{}/edit/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/users/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_user_unlock(self):
        # Staff setting is required to unlock users.
        self.user.is_staff = True
        self.user.save()

        entry = get_user_model().objects.first()
        url = "/users/{}/unlock/".format(entry.id)

        page = self.c.get(url)
        self.assertEqual(page.status_code, 200)
        page = self.c.post(url, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, UserUnlock.success_message)

    def test_welcome(self):
        page = self.c.get("/welcome/")
        self.assertEqual(page.status_code, 200)

    def test_logout_get_fails(self):
        page = self.c.get("/logout/")
        self.assertEqual(page.status_code, 405)

    @tag("isolate")
    def test_password_reset(self):
        """
        Testing this class primarily ensures Baby Buddy's custom templates are correctly
        configured for Django's password reset flow.
        """
        self.c.logout()

        page = self.c.get("/reset/")
        self.assertEqual(page.status_code, 200)

        page = self.c.post("/reset/", data={"email": self.user.email}, follow=True)
        self.assertEqual(page.status_code, 200)

        self.assertEqual(len(mail.outbox), 1)

        path = re.search(
            "http://testserver(?P<path>[^\\s]+)", mail.outbox[0].body
        ).group("path")
        page = self.c.get(path, follow=True)
        self.assertEqual(page.status_code, 200)

        new_password = "xZZVN6z4TvhFg6S"
        data = {
            "new_password1": new_password,
            "new_password2": new_password,
        }
        page = self.c.post(page.request["PATH_INFO"], data=data, follow=True)
        self.assertEqual(page.status_code, 200)
