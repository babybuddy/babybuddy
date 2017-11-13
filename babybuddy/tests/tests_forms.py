# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.test import Client as HttpClient

from faker import Factory


class FormsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(FormsTestCase, cls).setUpClass()
        fake = Factory.create()
        call_command('migrate', verbosity=0)
        call_command('fake', verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        cls.credentials = {
            'username': fake_user['username'],
            'password': fake.password()
        }
        cls.user = User.objects.create_user(
            is_superuser=True, **cls.credentials)

        cls.c.login(**cls.credentials)

    def test_user_settings(self):
        params = {
            'first_name': 'User',
            'last_name': 'Name',
            'email': 'user@user.user',
            'dashboard_refresh_rate': ''
        }

        page = self.c.post('/user/settings/', params)
        self.assertEqual(page.status_code, 302)

        params = {'email': 'Not an email address'}
        page = self.c.post('/user/settings/', params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'user_form', 'email',
                             'Enter a valid email address.')
