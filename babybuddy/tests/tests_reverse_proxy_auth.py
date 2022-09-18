# -*- coding: utf-8 -*-
from django.core.management import call_command
from django.test import Client as HttpClient, TestCase, modify_settings


class ReverseProxyAuthTestCase(TestCase):
    """
    Notes:
        - A class method cannot be used to establish the HTTP client because of the
          settings overrides required for these tests.
        - Overriding the `REVERSE_PROXY_AUTH` environment variable directly is not
          possible because environments variables are only evaluated once for the run.
    """

    def test_remote_user_authentication_disabled(self):
        call_command("migrate", verbosity=0)
        c = HttpClient()
        response = c.get("/welcome/", HTTP_REMOTE_USER="admin", follow=True)
        self.assertRedirects(response, "/login/?next=/welcome/")

    @modify_settings(
        MIDDLEWARE={"append": "babybuddy.middleware.CustomRemoteUser"},
        AUTHENTICATION_BACKENDS={
            "append": "django.contrib.auth.backends.RemoteUserBackend"
        },
    )
    def test_remote_user_authentication_enabled(self):
        call_command("migrate", verbosity=0)
        c = HttpClient()
        response = c.get("/welcome/", HTTP_REMOTE_USER="admin")
        self.assertEqual(response.status_code, 200)
