# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.test import Client as HttpClient
from django.utils import timezone

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
        params = {
            'first_name': 'Child',
            'last_name': 'One',
            'birth_date': '2000-01-01'
        }

        entry = models.Child.objects.first()
        page = self.c.post('/children/{}/edit/'.format(entry.slug), params)
        self.assertEqual(page.status_code, 302)
        entry.refresh_from_db()

        params = {'confirm_name': 'Incorrect'}
        page = self.c.post('/children/{}/delete/'.format(entry.slug), params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'confirm_name',
                             'Name does not match child name.')

        params['confirm_name'] = str(entry)
        page = self.c.post('/children/{}/delete/'.format(entry.slug), params)
        self.assertEqual(page.status_code, 302)

    def test_diaperchange_forms(self):
        params = {
            'child': 1,
            'time': '2000-01-01 1:01',
            'wet': 1,
            'solid': 1,
            'color': 'black'
        }

        entry = models.DiaperChange.objects.first()
        page = self.c.post('/changes/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 302)

        del params['solid']
        del params['wet']
        del params['color']
        page = self.c.post('/changes/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', None,
                             'Wet and/or solid is required.')

    def test_feeding_forms(self):
        entry = models.Feeding.objects.first()
        params = {
            'child': 1,
            'start': '2000-01-01 1:01',
            'end': '2000-01-01 1:31',
            'type': 'formula',
            'method': 'bottle',
            'amount': 0
        }

        timer = models.Timer.objects.create(user=self.user)
        timer.save()
        page = self.c.post('/feedings/add/?timer={}'.format(timer.id), params)
        self.assertEqual(page.status_code, 302)

        # Change start and end to prevent intersection validation errors.
        params['start'] = '2000-01-01 2:01'
        params['end'] = '2000-01-01 2:31'
        page = self.c.post('/feedings/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 302)

        params['method'] = 'left breast'
        page = self.c.post('/feedings/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page, 'form', 'method',
            'Only "Bottle" method is allowed with "Formula" type.')

    def test_sleep_forms(self):
        params = {
            'child': 1,
            'start': '2000-01-01 1:01',
            'end': '2000-01-01 3:01',
        }

        timer = models.Timer.objects.create(user=self.user)
        timer.save()
        page = self.c.post('/sleep/add/?timer={}'.format(timer.id), params)
        self.assertEqual(page.status_code, 302)

        # Change start and end to prevent intersection validation errors.
        params['start'] = '2000-01-01 4:01'
        params['end'] = '2000-01-01 6:01'
        entry = models.Sleep.objects.first()
        page = self.c.post('/sleep/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 302)

    def test_timer_forms(self):
        start_time = timezone.localtime()
        timer = models.Timer.objects.create(user=self.user, start=start_time)
        timer.save()

        params = {
            'name': 'New',
            'start': start_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        page = self.c.post('/timer/{}/edit/'.format(timer.id), params)
        self.assertEqual(page.status_code, 302)
        timer.refresh_from_db()
        self.assertEqual(timer.name, params['name'])

        # Test changing the timer start time.
        start_time = timer.start - timezone.timedelta(hours=1)
        params['start'] = timezone.localtime(start_time).strftime(
            '%Y-%m-%d %H:%M:%S')
        page = self.c.post('/timer/{}/edit/'.format(timer.id), params)
        self.assertEqual(page.status_code, 302)
        timer.refresh_from_db()
        self.assertEqual(timer.start, start_time)

        # Test changing a stopped timer
        timer.end = timer.start + timezone.timedelta(hours=1)
        timer.save()
        params['name'] = 'New timer name'
        page = self.c.post('/timer/{}/edit/'.format(timer.id), params)
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
        page = self.c.post(
            '/tummy-time/add/?timer={}'.format(timer.id), params)
        self.assertEqual(page.status_code, 302)

        # Change start and end to prevent intersection validation errors.
        params['start'] = '2000-01-01 2:01'
        params['end'] = '2000-01-01 2:11'
        entry = models.TummyTime.objects.first()
        page = self.c.post('/tummy-time/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 302)

    def test_weight_forms(self):
        params = {
            'child': 1,
            'weight': '8.5',
            'date': '2000-01-01'
        }

        entry = models.Weight.objects.first()
        page = self.c.post('/weight/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 302)

    def test_validate_date(self):
        future = (timezone.localdate() + timezone.timedelta(days=1))
        params = {
            'child': 1,
            'weight': '8.5',
            'date': future.strftime('%Y-%m-%d')
        }
        entry = models.Weight.objects.first()

        page = self.c.post('/weight/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'date',
                             'Date can not be in the future.')

    def test_validate_duration(self):
        params = {
            'child': 1,
            'start': '2001-01-01 1:01',
            'end': '2000-01-01 1:11',
            'milestone': ''
        }
        entry = models.TummyTime.objects.first()

        page = self.c.post('/tummy-time/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', None,
                             'Start time must come before end time.')

        params['start'] = '1999-01-01 1:11'
        page = self.c.post('/tummy-time/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', None, 'Duration too long.')

    def test_validate_time(self):
        future = (timezone.localtime() + timezone.timedelta(hours=1))
        params = {
            'child': 1,
            'start': timezone.localtime().strftime('%Y-%m-%d %H:%M:%S'),
            'end': future.strftime('%Y-%m-%d %H:%M:%S'),
            'milestone': ''
        }
        entry = models.TummyTime.objects.first()

        page = self.c.post('/tummy-time/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'end',
                             'Date/time can not be in the future.')

    def test_validate_unique_period(self):
        entry = models.TummyTime.objects.first()
        base_time = timezone.localtime()
        new_entry = models.TummyTime.objects.create(
            child=entry.child,
            start=base_time - timezone.timedelta(minutes=45),
            end=base_time - timezone.timedelta(minutes=15),
        )
        new_entry.save()

        params = {
            'child': 1,
            'start': (base_time - timezone.timedelta(minutes=35)).strftime(
                '%Y-%m-%d %H:%M'),
            'end': (base_time - timezone.timedelta(minutes=5)).strftime(
                '%Y-%m-%d %H:%M'),
            'milestone': ''
        }
        page = self.c.post('/tummy-time/{}/'.format(entry.id), params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page,
            'form',
            None,
            'Another entry intersects the specified time period.')
