# -*- coding: utf-8 -*-
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
