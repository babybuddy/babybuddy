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
    c = None
    child = None
    user = None

    @classmethod
    def setUpClass(cls):
        super(FormsTestCaseBase, cls).setUpClass()
        fake = Factory.create()
        call_command('migrate', verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        credentials = {
            'username': fake_user['username'],
            'password': fake.password()
        }
        cls.user = User.objects.create_user(
            is_superuser=True, **credentials)
        cls.c.login(**credentials)

        cls.child = models.Child.objects.create(
            first_name='Child',
            last_name='One',
            birth_date=timezone.localdate()
        )

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


class InitialValuesTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(InitialValuesTestCase, cls).setUpClass()
        cls.timer = models.Timer.objects.create(
            user=cls.user,
            start=timezone.localtime() - timezone.timedelta(minutes=30)
        )

    def test_child_with_one_child(self):
        page = self.c.get('/sleep/add/')
        self.assertEqual(page.context['form'].initial['child'], self.child)

    def test_child_with_parameter(self):
        child_two = models.Child.objects.create(
            first_name='Child',
            last_name='Two',
            birth_date=timezone.localdate()
        )

        page = self.c.get('/sleep/add/')
        self.assertTrue('child' not in page.context['form'].initial)

        page = self.c.get('/sleep/add/?child={}'.format(self.child.slug))
        self.assertEqual(page.context['form'].initial['child'], self.child)

        page = self.c.get('/sleep/add/?child={}'.format(child_two.slug))
        self.assertEqual(page.context['form'].initial['child'], child_two)

    def test_feeding_type(self):
        child_two = models.Child.objects.create(
            first_name='Child',
            last_name='Two',
            birth_date=timezone.localdate()
        )
        child_three = models.Child.objects.create(
            first_name='Child',
            last_name='Three',
            birth_date=timezone.localdate()
        )
        start_time = timezone.localtime() - timezone.timedelta(hours=4)
        end_time = timezone.localtime() - timezone.timedelta(hours=3,
                                                             minutes=30)
        f_one = models.Feeding.objects.create(
            child=self.child,
            start=start_time,
            end=end_time,
            type='breast milk',
            method='left breast'
        )
        f_two = models.Feeding.objects.create(
            child=child_two,
            start=start_time,
            end=end_time,
            type='formula',
            method='bottle'
        )
        f_three = models.Feeding.objects.create(
            child=child_three,
            start=start_time,
            end=end_time,
            type='fortified breast milk',
            method='bottle'
        )

        page = self.c.get('/feedings/add/')
        self.assertTrue('type' not in page.context['form'].initial)

        page = self.c.get('/feedings/add/?child={}'.format(self.child.slug))
        self.assertEqual(page.context['form'].initial['type'], f_one.type)
        self.assertFalse('method' in page.context['form'].initial)

        page = self.c.get('/feedings/add/?child={}'.format(child_two.slug))
        self.assertEqual(page.context['form'].initial['type'], f_two.type)
        self.assertEqual(page.context['form'].initial['method'], f_two.method)

        page = self.c.get('/feedings/add/?child={}'.format(child_three.slug))
        self.assertEqual(page.context['form'].initial['type'], f_three.type)
        self.assertEqual(page.context['form'].initial['method'],
                         f_three.method)

    def test_timer_set(self):
        self.timer.stop()

        page = self.c.get('/sleep/add/')
        self.assertTrue('start' not in page.context['form'].initial)
        self.assertTrue('end' not in page.context['form'].initial)

        page = self.c.get('/sleep/add/?timer={}'.format(self.timer.id))
        self.assertEqual(page.context['form'].initial['start'],
                         self.timer.start)
        self.assertEqual(page.context['form'].initial['end'], self.timer.end)

    def test_timer_stop_on_save(self):
        end = timezone.localtime()
        params = {
            'child': self.child.id,
            'start': self.localtime_string(self.timer.start),
            'end': self.localtime_string(end)
        }
        page = self.c.post('/sleep/add/?timer={}'.format(self.timer.id),
                           params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.timer.refresh_from_db()
        self.assertFalse(self.timer.active)
        self.assertEqual(self.localtime_string(self.timer.end), params['end'])


class ChildFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(ChildFormsTestCase, cls).setUpClass()
        cls.child = models.Child.objects.first()

    def test_add(self):
        params = {
            'first_name': 'Child',
            'last_name': 'Two',
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


class DiaperChangeFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(DiaperChangeFormsTestCase, cls).setUpClass()
        cls.change = models.DiaperChange.objects.create(
            child=cls.child,
            time=timezone.localtime(),
            wet=True,
            solid=True,
            color='black',
            amount=0.45
        )

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


class FeedingFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(FeedingFormsTestCase, cls).setUpClass()
        cls.feeding = models.Feeding.objects.create(
            child=cls.child,
            start=timezone.localtime() - timezone.timedelta(hours=2),
            end=timezone.localtime() - timezone.timedelta(hours=1, minutes=30),
            type='breast milk',
            method='left breast',
            amount=2.5
        )

    def test_add(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=30)
        params = {
            'child': self.child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
            'type': 'formula',
            'method': 'bottle',
            'amount': 0
        }
        page = self.c.post('/feedings/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Feeding entry for {} added'.format(str(self.child))
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


class SleepFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(SleepFormsTestCase, cls).setUpClass()
        cls.sleep = models.Sleep.objects.create(
            child=cls.child,
            start=timezone.localtime() - timezone.timedelta(hours=6),
            end=timezone.localtime() - timezone.timedelta(hours=4)
        )

    def test_add(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=2)
        params = {
            'child': self.child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
        }

        page = self.c.post('/sleep/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Sleep entry for {} added'.format(str(self.child))
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


class TemperatureFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TemperatureFormsTestCase, cls).setUpClass()
        cls.temp = models.Temperature.objects.create(
            child=cls.child,
            temperature=98.6,
            time=timezone.localtime() - timezone.timedelta(days=1)
        )

    def test_add(self):
        params = {
            'child': self.child.id,
            'temperature': '98.6',
            'time': self.localtime_string()
        }

        page = self.c.post('/temperature/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Temperature entry for {} added'.format(str(self.child))
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


class TummyTimeFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TummyTimeFormsTestCase, cls).setUpClass()
        cls.tt = models.TummyTime.objects.create(
            child=cls.child,
            start=timezone.localtime() - timezone.timedelta(hours=2),
            end=timezone.localtime() - timezone.timedelta(hours=1, minutes=50)
        )

    def test_add(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=2)
        params = {
            'child': self.child.id,
            'start': self.localtime_string(start),
            'end': self.localtime_string(end),
            'milestone': ''
        }

        page = self.c.post('/tummy-time/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Tummy Time entry for {} added'.format(str(self.child))
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


class TimerFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TimerFormsTestCase, cls).setUpClass()
        cls.timer = models.Timer.objects.create(user=cls.user)

    def test_add(self):
        params = {
            'child': self.child.id,
            'name': 'Test Timer',
            'start': self.localtime_string()
        }
        page = self.c.post('/timers/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, params['name'])
        self.assertContains(page, params['child'])

    def test_edit(self):
        start_time = self.timer.start - timezone.timedelta(hours=1)
        params = {
            'name': 'New Timer Name',
            'start': self.localtime_string(start_time)
        }
        page = self.c.post('/timers/{}/edit/'.format(self.timer.id), params,
                           follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, params['name'])
        self.timer.refresh_from_db()
        self.assertEqual(
            self.localtime_string(self.timer.start), params['start'])

    def test_edit_stopped(self):
        self.timer.stop()
        params = {
            'name': 'Edit stopped timer',
            'start': self.localtime_string(self.timer.start),
            'end': self.localtime_string(self.timer.end),
        }
        page = self.c.post('/timers/{}/edit/'.format(self.timer.id), params,
                           follow=True)
        self.assertEqual(page.status_code, 200)

    def test_delete_inactive(self):
        models.Timer.objects.create(user=self.user)
        self.assertEqual(models.Timer.objects.count(), 2)
        self.timer.stop()
        page = self.c.post('/timers/delete-inactive/', follow=True)
        self.assertEqual(page.status_code, 200)
        messages = list(page.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'All inactive timers deleted.')
        self.assertEqual(models.Timer.objects.count(), 1)


class ValidationsTestCase(FormsTestCaseBase):
    def test_validate_date(self):
        future = timezone.localtime() + timezone.timedelta(days=1)
        params = {
            'child': self.child,
            'weight': '8.5',
            'date': self.localdate_string(future)
        }
        entry = models.Weight.objects.create(**params)

        page = self.c.post('/weight/{}/'.format(entry.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'date',
                             'Date can not be in the future.')

    def test_validate_duration(self):
        end = timezone.localtime() - timezone.timedelta(minutes=10)
        start = end + timezone.timedelta(minutes=5)
        params = {
            'child': self.child,
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
        future = timezone.localtime() + timezone.timedelta(hours=1)
        params = {
            'child': self.child,
            'start': self.localtime_string(),
            'end': self.localtime_string(future),
            'milestone': ''
        }

        page = self.c.post('/tummy-time/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page, 'form', 'end',
                             'Date/time can not be in the future.')

    def test_validate_unique_period(self):
        entry = models.TummyTime.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=10),
            end=timezone.localtime() - timezone.timedelta(minutes=5),
        )

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


class WeightFormsTest(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(WeightFormsTest, cls).setUpClass()
        cls.weight = models.Weight.objects.create(
            child=cls.child,
            weight=8,
            date=timezone.localdate() - timezone.timedelta(days=2)
        )

    def test_add(self):
        params = {
            'child': self.child.id,
            'weight': 8.5,
            'date': self.localdate_string()
        }

        page = self.c.post('/weight/add/', params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page,
            'Weight entry for {} added'.format(str(self.child))
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
