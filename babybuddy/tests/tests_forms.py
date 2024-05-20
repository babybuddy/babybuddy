# -*- coding: utf-8 -*-
import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client as HttpClient, override_settings, TestCase
from django.utils import timezone

from faker import Faker


class FormsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(FormsTestCase, cls).setUpClass()
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

        cls.user_template = {
            "username": "username",
            "first_name": "User",
            "last_name": "Name",
            "email": "user@user.user",
            "is_staff": False,
            "is_read_only": False,
            "password1": "d47o8dD&#hu3ulu3",
            "password2": "d47o8dD&#hu3ulu3",
        }

        cls.settings_template = {
            "first_name": "User",
            "last_name": "Name",
            "email": "user@user.user",
            "dashboard_refresh_rate": "",
            "language": "en-US",
            "timezone": "UTC",
            "next": "/user/settings/",
            "pagination_count": 25,
        }

    def test_change_password(self):
        self.c.login(**self.credentials)

        page = self.c.get("/user/password/")
        self.assertEqual(page.status_code, 200)

        params = {
            "old_password": "wrong",
            "new_password1": "mynewpassword",
            "new_password2": "notmynewpassword",
        }

        page = self.c.post("/user/password/", params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page.context["form"],
            "old_password",
            "Your old password was entered incorrectly. " "Please enter it again.",
        )

        params["old_password"] = self.credentials["password"]
        page = self.c.post("/user/password/", params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page.context["form"],
            "new_password2",
            "The two password fields didn’t match.",
        )

        params["new_password2"] = "mynewpassword"
        page = self.c.post("/user/password/", params)
        self.assertEqual(page.status_code, 200)

    def test_user_forms(self):
        self.user.is_staff = True
        self.user.save()
        self.c.login(**self.credentials)
        params = self.user_template.copy()

        page = self.c.post("/users/add/", params)
        self.assertEqual(page.status_code, 302)
        new_user = get_user_model().objects.get(username="username")
        self.assertIsInstance(new_user, get_user_model())

        params["first_name"] = "Changed"
        page = self.c.post("/users/{}/edit/".format(new_user.id), params)
        self.assertEqual(page.status_code, 302)
        new_user.refresh_from_db()
        self.assertEqual(new_user.first_name, params["first_name"])

        page = self.c.post("/users/{}/delete/".format(new_user.id))
        self.assertEqual(page.status_code, 302)
        self.assertQuerySetEqual(
            get_user_model().objects.filter(username="username"), []
        )

    def test_add_regular_user(self):
        self.user.is_staff = True
        self.user.save()
        self.c.login(**self.credentials)

        params = self.user_template.copy()

        page = self.c.post("/users/add/", params)
        self.assertEqual(page.status_code, 302)
        user = get_user_model().objects.get(username="username")
        self.assertIsInstance(user, get_user_model())
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(
            user.groups.filter(
                name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
            ).exists()
        )

    def test_add_staff_user(self):
        self.user.is_staff = True
        self.user.save()
        self.c.login(**self.credentials)

        params = self.user_template.copy()
        params["is_staff"] = True

        page = self.c.post("/users/add/", params)
        self.assertEqual(page.status_code, 302)
        user = get_user_model().objects.get(username="username")
        self.assertIsInstance(user, get_user_model())
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertFalse(
            user.groups.filter(
                name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
            ).exists()
        )

    def test_add_read_only_user(self):
        self.user.is_staff = True
        self.user.save()
        self.c.login(**self.credentials)

        params = self.user_template.copy()
        params["is_read_only"] = True

        page = self.c.post("/users/add/", params)
        self.assertEqual(page.status_code, 302)
        user = get_user_model().objects.get(username="username")
        self.assertIsInstance(user, get_user_model())
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(
            user.groups.filter(
                name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
            ).exists()
        )

    def test_user_settings(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params["first_name"] = "New First Name"

        page = self.c.post("/user/settings/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "New First Name")

    def test_user_regenerate_api_key(self):
        self.c.login(**self.credentials)

        api_key_before = (
            get_user_model().objects.get(pk=self.user.id).settings.api_key()
        )

        params = self.settings_template.copy()
        params["api_key_regenerate"] = "Regenerate"

        page = self.c.post("/user/settings/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        new_api_key = get_user_model().objects.get(pk=self.user.id).settings.api_key()
        self.assertNotEqual(api_key_before, new_api_key)

        # API key can also be regenerated on the add-device page
        api_key_before = new_api_key
        params = {"api_key_regenerate": "Regenerate"}
        page = self.c.post("/user/add-device/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        new_api_key = get_user_model().objects.get(pk=self.user.id).settings.api_key()
        self.assertNotEqual(api_key_before, new_api_key)

    def test_invalid_post_to_add_device(self):
        self.c.login(**self.credentials)
        page = self.c.get("/user/add-device/")
        self.assertEqual(page.status_code, 200)
        page = self.c.post("/user/add-device/", params={"garbage": True}, follow=True)
        self.assertEqual(page.status_code, 400)

    def test_user_settings_invalid(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params["email"] = "Not an email address"

        page = self.c.post("/user/settings/", params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page.context["user_form"], "email", "Enter a valid email address."
        )

    def test_user_settings_language(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params["language"] = "fr"
        page = self.c.post("/user/settings/", data=params, follow=True)
        self.assertContains(page, "Paramètres utilisateur")

    def test_user_settings_timezone(self):
        self.c.login(**self.credentials)

        self.assertEqual(timezone.get_default_timezone_name(), "UTC")
        params = self.settings_template.copy()
        params["timezone"] = "US/Pacific"
        page = self.c.post("/user/settings/", data=params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(timezone.get_current_timezone_name(), params["timezone"])

    def test_user_settings_dashboard_hide_empty_on(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params["dashboard_hide_empty"] = "on"

        page = self.c.post("/user/settings/", data=params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.settings.dashboard_hide_empty)

    def test_user_settings_dashboard_refresh_rate(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params["dashboard_refresh_rate"] = "0:05:00"

        page = self.c.post("/user/settings/", data=params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.settings.dashboard_refresh_rate, datetime.timedelta(seconds=300)
        )

    def test_user_settings_pagination_count(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params["pagination_count"] = 25

        page = self.c.post("/user/settings/", data=params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.settings.pagination_count, 25)

    def test_user_settings_dashboard_hide_age(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params["dashboard_hide_age"] = "1 day, 0:00:00"

        page = self.c.post("/user/settings/", data=params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(
            self.user.settings.dashboard_hide_age, datetime.timedelta(days=1)
        )

    def test_csrf_error_handling(self):
        c = HttpClient(enforce_csrf_checks=True)
        c.login(**self.credentials)

        # Add a CSRF cookie to the client by making a request with the logout form.
        c.get("/", follow=True)

        # Send POST request with an invalid Origin.
        headers = {"HTTP_ORIGIN": "https://www.example.com"}
        data = {"csrfmiddlewaretoken": c.cookies["csrftoken"].value}
        response = c.post("/logout/", data=data, follow=True, **headers)

        # Assert response contains Baby Buddy's custom 403 handler text.
        self.assertContains(response, "How to Fix", status_code=403)

        response = c.post("/logout/", data=data, follow=True)
        self.assertEqual(response.status_code, 200)
