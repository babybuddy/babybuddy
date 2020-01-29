# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.test import Client as HttpClient
from django.utils import timezone
from django.utils.formats import get_format

from faker import Factory

from core import models


class FormsTestCaseBase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(FormsTestCaseBase, cls).setUpClass()
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

    @staticmethod
    def localdate_string(datetime=None):
        """ Converts an object to a local date string for form input. """
        date_format = get_format('DATE_INPUT_FORMATS')[0]
        return timezone.localdate(datetime).strftime(date_format)

    @staticmethod
    def localtime_string(datetime=None):
        """ Converts an object to a local time string for form input. """
        datetime_format = get_format('DATETIME_INPUT_FORMATS')[0]
        return timezone.localtime(datetime).strftime(datetime_format)


class FormValidationTestCase(FormsTestCaseBase):
    def test_validate_date(self):
        future = timezone.localtime() + timezone.timedelta(days=1)
        params = {
            'child': 1,
            'weight': '8.5',
            'date': self.localdate_string(future)
        }
        entry = models.Weight.objects.first()

        page = self.c.post('/weight/{}/'.format(entry.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'date',
                             'Date can not be in the future.')

    def test_validate_duration(self):
        child = models.Child.objects.first()
        end = timezone.localtime() - timezone.timedelta(minutes=10)
        start = end + timezone.timedelta(minutes=5)
        params = {
            'child': child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
            'milestone': ''
        }

        page = self.c.post('/tummy-time/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', None,
                             'Start time must come before end time.')

        start = end - timezone.timedelta(weeks=53)
        params['start'] = self.localtime_string(start)
        page = self.c.post('/tummy-time/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', None, 'Duration too long.')

    def test_validate_time(self):
        child = models.Child.objects.first()
        future = timezone.localtime() + timezone.timedelta(hours=1)
        params = {
            'child': child.id,
            'start': self.localtime_string(),
            'end': self.localtime_string(future),
            'milestone': ''
        }

        page = self.c.post('/tummy-time/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'end',
                             'Date/time can not be in the future.')

    def test_validate_unique_period(self):
        entry = models.TummyTime.objects.first()
        start = entry.start - timezone.timedelta(minutes=2)
        end = entry.end + timezone.timedelta(minutes=2)
        params = {
            'child': entry.child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
            'milestone': ''
        }

        page = self.c.post('/tummy-time/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page,
            'form',
            None,
            'Another entry intersects the specified time period.')


class ChildFormsTestCaseBase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(ChildFormsTestCaseBase, cls).setUpClass()
        cls.child = models.Child.objects.first()

    def test_add(self):
        params = {
            'first_name': 'Child',
            'last_name': 'One',
            'birth_date': timezone.localdate()
        }
        page = self.c.post('/children/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Child entry added')

    def test_edit(self):
        params = {
            'first_name': 'Name',
            'last_name': 'Changed',
            'birth_date': self.child.birth_date
        }
        page = self.c.post('/children/{}/edit/'.format(self.child.slug),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.child.refresh_from_db()
        self.assertEqual(self.child.last_name, params['last_name'])
        self.assertContains(page, 'Child entry updated')

    def test_delete(self):
        params = {'confirm_name': 'Incorrect'}
        page = self.c.post('/children/{}/delete/'.format(self.child.slug),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'confirm_name',
                             'Name does not match child name.')

        params['confirm_name'] = str(self.child)
        page = self.c.post('/children/{}/delete/'.format(self.child.slug),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Child entry deleted')


class DiaperChangeFormsTestCaseBase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(DiaperChangeFormsTestCaseBase, cls).setUpClass()
        cls.change = models.DiaperChange.objects.first()

    def test_add(self):
        child = models.Child.objects.first()
        params = {
            'child': child.id,
            'time': self.localtime_string(),
            'color': 'black',
            'amount': 0.45
        }
        page = self.c.post('/changes/add/', params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', None,
                             'Wet and/or solid is required.')

        params.update({'wet': 1, 'solid': 1, 'color': 'black'})
        page = self.c.post('/changes/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Diaper Change entry for {} added'.format(str(child))
        )

    def test_edit(self):
        params = {
            'child': self.change.child.id,
            'time': self.localtime_string(),
            'wet': self.change.wet,
            'solid': self.change.solid,
            'color': self.change.color,
            'amount': 1.23
        }
        page = self.c.post('/changes/{}/'.format(self.change.id),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.change.refresh_from_db()
        self.assertEqual(self.change.amount, params['amount'])
        self.assertContains(
            page,
            'Diaper Change entry for {} updated'.format(str(self.change.child))
        )

    def test_delete(self):
        page = self.c.post('/changes/{}/delete/'.format(self.change.id),
                           follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Diaper Change entry deleted')


class FeedingFormsTestCaseBase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(FeedingFormsTestCaseBase, cls).setUpClass()
        cls.feeding = models.Feeding.objects.first()

    def test_add(self):
        child = models.Child.objects.first()
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=30)
        params = {
            'child': child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
            'type': 'formula',
            'method': 'left breast',
            'amount': 0
        }
        page = self.c.post('/feedings/add/', params)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page, 'form', 'method',
            'Only "Bottle" method is allowed with "Formula" type.')

        params.update({'method': 'bottle'})
        page = self.c.post('/feedings/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Feeding entry for {} added'.format(str(child))
        )

    def test_edit(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=30)
        params = {
            'child': self.feeding.child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
            'type': self.feeding.type,
            'method': self.feeding.method,
            'amount': 100
        }
        page = self.c.post('/feedings/{}/'.format(self.feeding.id),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.feeding.refresh_from_db()
        self.assertEqual(self.feeding.amount, params['amount'])
        self.assertContains(
            page,
            'Feeding entry for {} updated'.format(str(self.feeding.child))
        )

    def test_delete(self):
        page = self.c.post('/feedings/{}/delete/'.format(self.feeding.id),
                           follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Feeding entry deleted')


class SleepFormsTestCaseBase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(SleepFormsTestCaseBase, cls).setUpClass()
        cls.sleep = models.Sleep.objects.first()

    def test_add(self):
        child = models.Child.objects.first()
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=2)
        params = {
            'child': child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
        }

        page = self.c.post('/sleep/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Sleep entry for {} added'.format(str(child))
        )

    def test_edit(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=2)
        params = {
            'child': self.sleep.child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
        }
        page = self.c.post('/sleep/{}/'.format(self.sleep.id),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.sleep.refresh_from_db()
        self.assertEqual(
            self.localtime_string(self.sleep.end),
            params['end']
        )
        self.assertContains(
            page,
            'Sleep entry for {} updated'.format(str(self.sleep.child))
        )

    def test_delete(self):
        page = self.c.post('/sleep/{}/delete/'.format(self.sleep.id),
                           follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Sleep entry deleted')


class TemperatureFormsTestCaseBase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TemperatureFormsTestCaseBase, cls).setUpClass()
        cls.temp = models.Temperature.objects.first()

    def test_add(self):
        child = models.Child.objects.first()
        params = {
            'child': child.id,
            'temperature': '98.6',
            'time': self.localtime_string()
        }

        page = self.c.post('/temperature/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Temperature entry for {} added'.format(str(child))
        )

    def test_edit(self):
        params = {
            'child': self.temp.child.id,
            'temperature': self.temp.temperature + 2,
            'time': self.localtime_string()
        }
        page = self.c.post('/temperature/{}/'.format(self.temp.id),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.temp.refresh_from_db()
        self.assertEqual(self.temp.temperature, params['temperature'])
        self.assertContains(
            page,
            'Temperature entry for {} updated'.format(str(self.temp.child))
        )

    def test_delete(self):
        page = self.c.post('/temperature/{}/delete/'.format(self.temp.id),
                           follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Temperature entry deleted')


class TummyTimeFormsTestCaseBase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TummyTimeFormsTestCaseBase, cls).setUpClass()
        cls.tt = models.TummyTime.objects.first()

    def test_add(self):
        child = models.Child.objects.first()
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=2)
        params = {
            'child': child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
            'milestone': ''
        }

        page = self.c.post('/tummy-time/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Tummy Time entry for {} added'.format(str(child))
        )

    def test_edit(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=1, seconds=32)
        params = {
            'child': self.tt.child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
            'milestone': 'Moved head!'
        }
        page = self.c.post('/tummy-time/{}/'.format(self.tt.id),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.tt.refresh_from_db()
        self.assertEqual(self.tt.milestone, params['milestone'])
        self.assertContains(
            page,
            'Tummy Time entry for {} updated'.format(str(self.tt.child))
        )

    def test_delete(self):
        page = self.c.post('/tummy-time/{}/delete/'.format(self.tt.id),
                           follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Tummy Time entry deleted')


class TimerFormsTestCaseBase(FormsTestCaseBase):
    def test_add(self):
        child = models.Child.objects.first()
        params = {
            'child': child.id,
            'name': 'Test Timer',
            'start': self.localtime_string()
        }
        page = self.c.post('/timer/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, params['name'])
        self.assertContains(page, params['child'])

    def test_edit(self):
        timer = models.Timer.objects.create(user=self.user)

        start_time = timer.start - timezone.timedelta(hours=1)
        params = {
            'name': 'New Timer Name',
            'start': self.localtime_string(start_time)
        }
        page = self.c.post('/timer/{}/edit/'.format(timer.id), params,
                           follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, params['name'])
        timer.refresh_from_db()
        self.assertEqual(self.localtime_string(timer.start), params['start'])


class WeightFormsTest(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(WeightFormsTest, cls).setUpClass()
        cls.weight = models.Weight.objects.first()

    def test_add(self):
        child = models.Child.objects.first()
        params = {
            'child': child.id,
            'weight': 8.5,
            'date': self.localdate_string()
        }

        page = self.c.post('/weight/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Weight entry for {} added'.format(str(child))
        )

    def test_edit(self):
        params = {
            'child': self.weight.child.id,
            'weight': self.weight.weight + 1,
            'date': self.localdate_string()
        }
        page = self.c.post('/weight/{}/'.format(self.weight.id),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.weight.refresh_from_db()
        self.assertEqual(self.weight.weight, params['weight'])
        self.assertContains(
            page,
            'Weight entry for {} updated'.format(str(self.weight.child))
        )

    def test_delete(self):
        page = self.c.post('/weight/{}/delete/'.format(self.weight.id),
                           follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, 'Weight entry deleted')
