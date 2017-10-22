# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth.models import User
from django.core.management import call_command

from faker import Factory

from core import models


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

    def test_child_forms(self):
        entry = models.Child.objects.first()
        page = self.c.post('/children/{}/edit/'.format(entry.slug), {
            'first_name': 'Child',
            'last_name': 'One',
            'birth_date': '2000-01-01'
        })
        self.assertEqual(page.status_code, 302)

    def test_diaperchange_forms(self):
        entry = models.DiaperChange.objects.first()
        page = self.c.post('/changes/{}/'.format(entry.id), {
            'child': 1,
            'time': '2000-01-01 1:01',
            'wet': 1,
            'solid': 1,
            'color': entry.color
        })
        self.assertEqual(page.status_code, 302)

    def test_feeding_forms(self):
        entry = models.Feeding.objects.first()
        params = {
            'child': 1,
            'start': '2000-01-01 1:01',
            'end': '2000-01-01 1:31',
            'type': entry.type,
            'method': entry.method,
            'amount': 0
        }

        timer = models.Timer.objects.create(user=self.user)
        timer.save()
        page = self.c.post('/feedings/add/?timer={}'.format(timer.id), params)
        self.assertEqual(page.status_code, 302)

        page = self.c.post('/feedings/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 302)

    def test_sleeping_forms(self):
        params = {
            'child': 1,
            'start': '2000-01-01 1:01',
            'end': '2000-01-01 3:01',
        }

        timer = models.Timer.objects.create(user=self.user)
        timer.save()
        page = self.c.post('/sleep/add/?timer={}'.format(timer.id), params)
        self.assertEqual(page.status_code, 302)

        entry = models.Sleep.objects.first()
        page = self.c.post('/sleep/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 302)

    def test_timer_forms(self):
        timer = models.Timer.objects.create(user=self.user)
        timer.save()
        # Post to test custom get_success_url() method.
        page = self.c.post('/timer/{}/edit/'.format(timer.id), {'name': 'New'})
        self.assertEqual(page.status_code, 302)

    def test_tummytime_forms(self):
        params = {
            'child': 1,
            'start': '2000-01-01 1:01',
            'end': '2000-01-01 1:11',
            'milestone': ''
        }

        timer = models.Timer.objects.create(user=self.user)
        timer.save()
        page = self.c.post('/tummy-time/add/?timer={}'.format(timer.id), params)
        self.assertEqual(page.status_code, 302)

        entry = models.TummyTime.objects.first()
        page = self.c.post('/tummy-time/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 302)
