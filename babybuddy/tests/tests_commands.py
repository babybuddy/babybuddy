# -*- coding: utf-8 -*-
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.management import call_command

from core.models import Child


class CommandsTestCase(TransactionTestCase):
    def test_migrate(self):
        call_command("migrate", verbosity=0)
        self.assertIsInstance(
            get_user_model().objects.get(username="admin"), get_user_model()
        )

    def test_fake(self):
        call_command("migrate", verbosity=0)
        call_command("fake", children=1, days=7, verbosity=0)
        self.assertEqual(Child.objects.count(), 1)
        call_command("fake", children=2, days=7, verbosity=0)
        self.assertEqual(Child.objects.count(), 3)

    def test_reset(self):
        call_command("reset", verbosity=0, interactive=False)
        self.assertIsInstance(
            get_user_model().objects.get(username="admin"), get_user_model()
        )
        self.assertEqual(Child.objects.count(), 1)

    def test_createuser(self):
        call_command(
            "createuser",
            username="test",
            email="test@test.test",
            password="test",
            verbosity=0,
        )
        self.assertIsInstance(
            get_user_model().objects.get(username="test"), get_user_model()
        )
        self.assertFalse(
            get_user_model().objects.filter(
                username="test", is_staff=True, is_superuser=True
            )
        )
        call_command(
            "createuser",
            "--is-staff",
            username="testadmin",
            email="testadmin@testadmin.testadmin",
            password="test",
            verbosity=0,
        )
        self.assertIsInstance(
            get_user_model().objects.get(username="testadmin"), get_user_model()
        )
        self.assertTrue(
            get_user_model().objects.filter(
                username="testadmin", is_staff=True, is_superuser=True
            )
        )
