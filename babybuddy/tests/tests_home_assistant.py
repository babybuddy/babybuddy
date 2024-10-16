import json

from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth import get_user_model
from django.core.management import call_command

from faker import Faker


class HomeAssistantMiddlewareTestCase(TestCase):
    """
    Tests are executed on the REST-API because that one constructs
    full absolute URLs. However, the middleware is part of the babybuddy
    so the test lives in here.
    """

    @classmethod
    def setUpClass(cls):
        super(HomeAssistantMiddlewareTestCase, cls).setUpClass()
        fake = Faker()
        call_command("migrate", verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        cls.credentials = {
            "username": fake_user["username"],
            "password": fake.password(),
        }
        cls.user = get_user_model().objects.create_user(
            is_superuser=True, is_staff=True, **cls.credentials
        )

    def test_no_ingress_request(self):
        self.c.login(**self.credentials)

        response = self.c.get("/api/", headers={"Accept": "application/json"})
        json_response = json.loads(response.content)

        self.assertEqual(json_response["profile"], "http://testserver/api/profile")

    def test_ingress_request_no_x_ingress_path(self):
        self.c.login(**self.credentials)

        response = self.c.get(
            "/api/",
            headers={"Accept": "application/json", "X-Hass-Source": "core.ingress"},
        )
        json_response = json.loads(response.content)

        self.assertEqual(json_response["profile"], "http://testserver/api/profile")

    def test_ingress_request_with_x_ingress_path(self):
        self.c.login(**self.credentials)

        response = self.c.get(
            "/api/",
            headers={
                "Accept": "application/json",
                "X-Hass-Source": "core.ingress",
                "X-Ingress-Path": "/magic/sub/url",
            },
        )
        json_response = json.loads(response.content)

        self.assertEqual(
            json_response["profile"], "http://testserver/magic/sub/url/api/profile"
        )
