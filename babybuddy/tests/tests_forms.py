# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client as HttpClient, override_settings, TestCase
from django.utils import timezone

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

        cls.settings_template = {
            'first_name': 'User',
            'last_name': 'Name',
            'email': 'user@user.user',
            'dashboard_refresh_rate': '',
            'language': 'en',
            'timezone': timezone.get_default_timezone_name(),
            'next': '/user/settings/'
        }

    def test_change_password(self):
        self.c.login(**self.credentials)

        page = self.c.get('/user/password/')
        self.assertEqual(page.status_code, 200)

        params = {
            'old_password': 'wrong',
            'new_password1': 'mynewpassword',
            'new_password2': 'notmynewpassword'
        }

        page = self.c.post('/user/password/', params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'old_password',
                             'Your old password was entered incorrectly. '
                             'Please enter it again.')

        params['old_password'] = self.credentials['password']
        page = self.c.post('/user/password/', params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'new_password2',
                             "The two password fields didn’t match.")

        params['new_password2'] = 'mynewpassword'
        page = self.c.post('/user/password/', params)
        self.assertEqual(page.status_code, 200)

    def test_user_forms(self):
        self.user.is_staff = True
        self.user.save()
        self.c.login(**self.credentials)

        params = {
            'username': 'username',
            'first_name': 'User',
            'last_name': 'Name',
            'email': 'user@user.user',
            'password1': 'password',
            'password2': 'password'
        }

        page = self.c.post('/users/add/', params)
        self.assertEqual(page.status_code, 302)
        new_user = User.objects.get(username='username')
        self.assertIsInstance(new_user, User)

        params['first_name'] = 'Changed'
        page = self.c.post('/users/{}/edit/'.format(new_user.id), params)
        self.assertEqual(page.status_code, 302)
        new_user.refresh_from_db()
        self.assertEqual(new_user.first_name, params['first_name'])

        page = self.c.post('/users/{}/delete/'.format(new_user.id))
        self.assertEqual(page.status_code, 302)
        self.assertQuerysetEqual(User.objects.filter(username='username'), [])

    def test_user_settings(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params['first_name'] = 'New First Name'

        page = self.c.post('/user/settings/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'New First Name')

    def test_user_settings_invalid(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params['email'] = 'Not an email address'

        page = self.c.post('/user/settings/', params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'user_form', 'email',
                             'Enter a valid email address.')

    def test_user_settings_language(self):
        self.c.login(**self.credentials)

        params = self.settings_template.copy()
        params['language'] = 'fr'
        page = self.c.post('/user/settings/', data=params, follow=True)
        self.assertContains(page, 'Paramètres Utilisateur')

    @override_settings(TIME_ZONE='US/Eastern')
    def test_user_settings_timezone(self):
        self.c.login(**self.credentials)

        self.assertEqual(timezone.get_default_timezone_name(), 'US/Eastern')
        params = self.settings_template.copy()
        params['timezone'] = 'US/Pacific'
        page = self.c.post('/user/settings/', data=params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(timezone.get_current_timezone_name(),
                         params['timezone'])
