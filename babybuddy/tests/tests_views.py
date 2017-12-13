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

    def test_root_router(self):
        page = self.c.get('/')
        self.assertEqual(page.url, '/welcome/')

        call_command('fake', verbosity=0, children=1, days=1)
        child = Child.objects.first()
        page = self.c.get('/')
        self.assertEqual(
            page.url, '/children/{}/dashboard/'.format(child.slug))

        Child.objects.create(
            first_name='Second',
            last_name='Child',
            birth_date='2000-01-01'
        )
        page = self.c.get('/')
        self.assertEqual(page.url, '/dashboard/')

    def test_user_reset_api_key(self):
        api_key_before = User.objects.get(pk=self.user.id).settings.api_key()
        page = self.c.get('/user/reset-api-key/')
        self.assertEqual(page.status_code, 302)
        self.assertNotEqual(
            api_key_before,
            User.objects.get(pk=self.user.id).settings.api_key()
        )

    def test_user_settings(self):
        page = self.c.get('/user/settings/')
        self.assertEqual(page.status_code, 200)

    def test_user_views(self):
        # Staff setting is required to access user management.
        page = self.c.get('/users/')
        self.assertEqual(page.status_code, 302)
        self.user.is_staff = True
        self.user.save()

        page = self.c.get('/users/')
        self.assertEqual(page.status_code, 200)
        page = self.c.get('/users/add/')
        self.assertEqual(page.status_code, 200)

        entry = User.objects.first()
        page = self.c.get('/users/{}/edit/'.format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('/users/{}/delete/'.format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_welcome(self):
        page = self.c.get('/welcome/')
        self.assertEqual(page.status_code, 200)
