# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth.models import User
from django.core.management import call_command

from faker import Factory

from core.models import Child


class ViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(ViewsTestCase, cls).setUpClass()
        fake = Factory.create()
        call_command('migrate', verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        cls.credentials = {
            'username': fake_user['username'],
            'password': fake.password()
        }
        cls.user = User.objects.create_user(
            is_superuser=True, **cls.credentials)

        cls.c.login(**cls.credentials)

    def test_dashboard_views(self):
        page = self.c.get('/dashboard/')
        self.assertEqual(page.status_code, 200)

        """ Dashboard handles the root URL and redirects based on zero, one, or
        more than one child is in the database."""
        page = self.c.get('/')
        self.assertEqual(page.url, '/children/add/')

        call_command('fake', verbosity=0, children=1)
        child = Child.objects.first()
        page = self.c.get('/')
        self.assertEqual(
            page.url, '/children/{}/dashboard/'.format(child.slug))
        # Test the actual child dashboard (including cards).
        # TODO: Test cards more granularly.
        page = self.c.get('/children/{}/dashboard/'.format(child.slug))
        self.assertEqual(page.status_code, 200)

        Child.objects.create(
            first_name='Second',
            last_name='Child',
            birth_date='2000-01-01'
        )
        page = self.c.get('/')
        self.assertEqual(page.url, '/dashboard/')
