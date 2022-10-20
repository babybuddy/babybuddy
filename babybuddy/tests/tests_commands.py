# -*- coding: utf-8 -*-
from django.test import TransactionTestCase
from django.contrib.auth.models import User, Group
from django.core.management import call_command

from core.models import Child


class CommandsTestCase(TransactionTestCase):
    def test_migrate(self):
        call_command("migrate", verbosity=0)
        self.assertIsInstance(User.objects.get(username="admin"), User)

    def test_fake(self):
        call_command("migrate", verbosity=0)
        call_command("fake", children=1, days=7, verbosity=0)
        self.assertEqual(Child.objects.count(), 1)
        call_command("fake", children=2, days=7, verbosity=0)
        self.assertEqual(Child.objects.count(), 3)

    def test_reset(self):
        call_command("reset", verbosity=0, interactive=False)
        self.assertIsInstance(User.objects.get(username="admin"), User)
        self.assertEqual(Child.objects.count(), 1)

    def test_createuser(self):
        Group.objects.create(name="read_only")
        Group.objects.create(name="staff")

        call_command(
            "createuser",
            username="test",
            email="test@test.test",
            password="test",
            verbosity=0,
        )
        self.assertIsInstance(User.objects.get(username="test"), User)
        self.assertFalse(User.objects.filter(username="test", is_staff=True))
        call_command(
            "createuser",
            username="testadmin",
            email="testadmin@testadmin.testadmin",
            password="test",
            group="staff",
            verbosity=0,
        )
        self.assertIsInstance(User.objects.get(username="testadmin"), User)
        self.assertTrue(User.objects.filter(username="testadmin", is_staff=True))
