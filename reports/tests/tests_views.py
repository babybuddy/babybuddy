# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth.models import User
from django.core.management import call_command
from django.utils import timezone

from faker import Factory

from core import models


class ViewsTestCase(TestCase):
    fixtures = ['tests.json']

    @classmethod
    def setUpClass(cls):
        super(ViewsTestCase, cls).setUpClass()
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

    def test_graph_child_views(self):
        child = models.Child.objects.first()
        base_url = '/children/{}/reports'.format(child.slug)

        page = self.c.get('{}/changes/amounts/'.format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('{}/changes/lifetimes/'.format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('{}/changes/types/'.format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get('{}/feeding/amounts/'.format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('{}/feeding/duration/'.format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get('{}/sleep/pattern/'.format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('{}/sleep/totals/'.format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get('{}/statistics/'.format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get('{}/weight/weight/'.format(base_url))
        self.assertEqual(page.status_code, 200)

    def test_report_statistics(self):
        child = models.Child.objects.first()
        base_url = '/children/{}/reports'.format(child.slug)
        page = self.c.get('{}/statistics/'.format(base_url))
        stats = [
            {'type': 'duration', 'stat': timezone.timedelta(seconds=44228, microseconds=571429),
             'title': 'Diaper change frequency'},
            {'type': 'duration', 'stat': 0.0, 'title': 'Feeding frequency (past 3 days)'},
            {'type': 'duration', 'stat': 0.0, 'title': 'Feeding frequency (past 2 weeks)'},
            {'type': 'duration', 'stat': timezone.timedelta(seconds=7200), 'title': 'Feeding frequency'},
            {'type': 'duration', 'stat': timezone.timedelta(seconds=7200), 'title': 'Average nap duration'},
            {'type': 'float', 'stat': 1.0, 'title': 'Average naps per day'},
            {'type': 'duration', 'stat': timezone.timedelta(seconds=6750), 'title': 'Average sleep duration'},
            {'type': 'duration', 'stat': timezone.timedelta(seconds=19200), 'title': 'Average awake duration'},
            {'type': 'float', 'stat': 1.0, 'title': 'Weight change per week'}
        ]
        self.assertEqual(page.context['stats'], stats)
