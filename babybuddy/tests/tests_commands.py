# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.management import call_command

from core.models import Child


class CommandsTestCase(TestCase):
    def test_migrate(self):
        call_command('migrate', verbosity=0)
        self.assertIsInstance(User.objects.get(username='admin'), User)

    def test_fake(self):
        call_command('migrate', verbosity=0)
        call_command('fake', children=1, days=7, verbosity=0)
        self.assertEqual(Child.objects.count(), 1)
        call_command('fake', children=2, days=7, verbosity=0)
        self.assertEqual(Child.objects.count(), 3)

    """def test_reset(self):
        call_command('reset', verbosity=0, interactive=False)
        self.assertIsInstance(User.objects.get(username='admin'), User)
        self.assertEqual(Child.objects.count(), 1)"""
