# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth.models import User
from django.core.management import call_command

from faker import Factory


class TranslationTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(TranslationTestCase, cls).setUpClass()
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

        cls.params_template = {
            'first_name': 'User',
            'last_name': 'Name',
            'email': 'user@user.user',
            'dashboard_refresh_rate': '',
            'language': 'en'
        }

        cls.c.login(**cls.credentials)

    def test_translation_fr(self):
        params = self.params_template.copy()
        params['language'] = 'fr'

        page = self.c.post('/user/settings/', data=params, follow=True)
        self.assertContains(page, 'Paramètres Utilisateur')

        page = self.c.get('/welcome/')
        self.assertContains(page, 'Bienvenue à Baby Buddy!')
