# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from webhooks.models import WebhookEndpoint


class WebhookEndpointTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)

    def test_a_new_endpoint_can_sign(self):
        endpoint = WebhookEndpoint.objects.create(
            name="Home", url="http://home.test/hook"
        )
        self.assertTrue(endpoint.secret)

    def test_endpoints_do_not_share_a_secret(self):
        one = WebhookEndpoint.objects.create(name="One", url="http://one.test/hook")
        two = WebhookEndpoint.objects.create(name="Two", url="http://two.test/hook")
        self.assertNotEqual(one.secret, two.secret)

    def test_a_secret_is_given(self):
        endpoint = WebhookEndpoint.objects.create(
            name="Home", url="http://home.test/hook", secret="mine"
        )
        self.assertEqual(endpoint.secret, "mine")

    def test_an_endpoint_must_use_a_scheme_that_is_delivered_to(self):
        # Django's own URL validators also allow ftp and ftps, which the sender
        # never uses, so an endpoint with one would be saved and then fail on
        # every delivery until its attempts ran out.
        endpoint = WebhookEndpoint(name="Elsewhere", url="ftp://home.test/hook")
        with self.assertRaises(ValidationError):
            endpoint.full_clean()
