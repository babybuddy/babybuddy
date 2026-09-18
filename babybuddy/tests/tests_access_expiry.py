from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AccessExpiryTestCase(APITestCase):
    fixtures = ["tests.json"]

    def setUp(self):
        self.credentials = {"username": "weekend-sitter", "password": "sitter"}
        self.user = get_user_model().objects.create_user(
            is_superuser=True, **self.credentials
        )
        self.token = Token.objects.create(user=self.user)

    def expire_in(self, delta):
        self.user.settings.access_expires = (
            None if delta is None else timezone.now() + delta
        )
        self.user.settings.save()

    def api_status(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        status = self.client.get(reverse("api:child-list")).status_code
        self.client.credentials()
        return status

    def test_access_before_expiry(self):
        self.expire_in(timezone.timedelta(hours=1))
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/children/").status_code, 200)
        self.client.logout()
        self.assertEqual(self.api_status(), 200)

    def test_expired_session_is_signed_out(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get("/children/").status_code, 200)
        self.expire_in(-timezone.timedelta(minutes=1))
        response = self.client.get("/children/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)
        self.assertNotIn("_auth_user_id", self.client.session)
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertIn("Your access has expired.", messages)

    def test_expired_api_key_is_refused(self):
        self.assertEqual(self.api_status(), 200)
        self.expire_in(-timezone.timedelta(minutes=1))
        self.assertIn(self.api_status(), (401, 403))

    def test_expired_user_cannot_sign_in(self):
        self.expire_in(-timezone.timedelta(minutes=1))
        response = self.client.post(
            reverse("babybuddy:login"), self.credentials, follow=True
        )
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_clearing_expiry_restores_access(self):
        self.expire_in(-timezone.timedelta(minutes=1))
        self.assertIn(self.api_status(), (401, 403))
        self.expire_in(None)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertEqual(self.api_status(), 200)

    def test_user_form_sets_and_clears_expiry(self):
        get_user_model().objects.create_user(
            username="staff", password="staff", is_superuser=True, is_staff=True
        )
        self.client.login(username="staff", password="staff")
        params = {
            "username": self.user.username,
            "first_name": "Weekend",
            "last_name": "Sitter",
            "email": "sitter@example.com",
            "is_active": True,
            "access_expires": "2030-01-02 03:04:00",
        }
        response = self.client.post(f"/users/{self.user.pk}/edit/", params)
        self.assertEqual(response.status_code, 302)
        self.user.settings.refresh_from_db()
        self.assertEqual(
            timezone.localtime(self.user.settings.access_expires).strftime(
                "%Y-%m-%d %H:%M"
            ),
            "2030-01-02 03:04",
        )
        params["access_expires"] = ""
        response = self.client.post(f"/users/{self.user.pk}/edit/", params)
        self.assertEqual(response.status_code, 302)
        self.user.settings.refresh_from_db()
        self.assertIsNone(self.user.settings.access_expires)

    def test_user_cannot_change_own_expiry(self):
        expires = timezone.now() + timezone.timedelta(hours=1)
        self.user.settings.access_expires = expires
        self.user.settings.save()
        self.client.force_login(self.user)
        self.client.post(
            "/user/settings/",
            {
                "first_name": "Weekend",
                "last_name": "Sitter",
                "email": "sitter@example.com",
                "dashboard_refresh_rate": "",
                "dashboard_hide_empty": False,
                "dashboard_hide_age": "",
                "language": "en-US",
                "timezone": "UTC",
                "pagination_count": 25,
                "access_expires": "",
            },
        )
        self.user.settings.refresh_from_db()
        self.assertEqual(self.user.settings.access_expires, expires)
