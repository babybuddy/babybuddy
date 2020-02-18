# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core import models


class ChildTestCase(TestCase):
    def setUp(self):
        call_command('migrate', verbosity=0)

    def test_child_create(self):
        child = models.Child.objects.create(
            first_name='First',
            last_name='Last',
            birth_date=timezone.localdate()
        )
        self.assertEqual(child, models.Child.objects.get(first_name='First'))
        self.assertEqual(child.slug, 'first-last')
        self.assertEqual(str(child), 'First Last')
        self.assertEqual(child.name(), 'First Last')
        self.assertEqual(child.name(reverse=True), 'Last, First')

    def test_child_count(self):
        self.assertEqual(models.Child.count(), 0)
        models.Child.objects.create(
            first_name='First 1',
            last_name='Last 1',
            birth_date=timezone.localdate()
        )
        self.assertEqual(models.Child.count(), 1)
        child = models.Child.objects.create(
            first_name='First 2',
            last_name='Last 2',
            birth_date=timezone.localdate()
        )
        self.assertEqual(models.Child.count(), 2)
        child.delete()
        self.assertEqual(models.Child.count(), 1)


class DiaperChangeTestCase(TestCase):
    def setUp(self):
        call_command('migrate', verbosity=0)
        self.child = models.Child.objects.create(
            first_name='First',
            last_name='Last',
            birth_date=timezone.localdate()
        )
        self.change = models.DiaperChange.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=1),
            wet=1,
            solid=1,
            color='black',
            amount=1.25
        )

    def test_diaperchange_create(self):
        self.assertEqual(self.change, models.DiaperChange.objects.first())
        self.assertEqual(str(self.change), 'Diaper Change')
        self.assertEqual(self.change.child, self.child)
        self.assertTrue(self.change.wet)
        self.assertTrue(self.change.solid)
        self.assertEqual(self.change.color, 'black')
        self.assertEqual(self.change.amount, 1.25)

    def test_diaperchange_attributes(self):
        self.assertListEqual(
            self.change.attributes(), ['Wet', 'Solid', 'Black'])


class FeedingTestCase(TestCase):
    def setUp(self):
        call_command('migrate', verbosity=0)
        self.child = models.Child.objects.create(
            first_name='First',
            last_name='Last',
            birth_date=timezone.localdate()
        )

    def test_feeding_create(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type='formula',
            method='bottle',
            amount=2
        )
        self.assertEqual(feeding, models.Feeding.objects.first())
        self.assertEqual(str(feeding), 'Feeding')
        self.assertEqual(feeding.duration, feeding.end - feeding.start)

    def test_method_both_breasts(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type='breast milk',
            method='both breasts'
        )
        self.assertEqual(feeding, models.Feeding.objects.first())
        self.assertEqual(str(feeding), 'Feeding')
        self.assertEqual(feeding.method, 'both breasts')


class NoteTestCase(TestCase):
    def setUp(self):
        call_command('migrate', verbosity=0)
        self.child = models.Child.objects.create(
            first_name='First',
            last_name='Last',
            birth_date=timezone.localdate()
        )

    def test_note_create(self):
        note = models.Note.objects.create(
            child=self.child, note='Note', time=timezone.localtime())
        self.assertEqual(note, models.Note.objects.first())
        self.assertEqual(str(note), 'Note')


class SleepTestCase(TestCase):
    def setUp(self):
        call_command('migrate', verbosity=0)
        self.child = models.Child.objects.create(
            first_name='First',
            last_name='Last',
            birth_date=timezone.localdate()
        )

    def test_sleep_create(self):
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
        )
        self.assertEqual(sleep, models.Sleep.objects.first())
        self.assertEqual(str(sleep), 'Sleep')
        self.assertEqual(sleep.duration, sleep.end - sleep.start)


class TemperatureTestCase(TestCase):
    def setUp(self):
        call_command('migrate', verbosity=0)
        self.child = models.Child.objects.create(
            first_name='First',
            last_name='Last',
            birth_date=timezone.localdate()
        )
        self.temp = models.Temperature.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=1),
            temperature=98.6
        )

    def test_temperature_create(self):
        self.assertEqual(self.temp, models.Temperature.objects.first())
        self.assertEqual(str(self.temp), 'Temperature')
        self.assertEqual(self.temp.temperature, 98.6)


class TimerTestCase(TestCase):
    def setUp(self):
        call_command('migrate', verbosity=0)
        child = models.Child.objects.create(
            first_name='First',
            last_name='Last',
            birth_date=timezone.localdate()
        )
        self.user = User.objects.first()
        self.named = models.Timer.objects.create(
            name='Named',
            end=timezone.localtime(),
            user=self.user,
            child=child
        )
        self.unnamed = models.Timer.objects.create(
            end=timezone.localtime(),
            user=self.user
        )

    def test_timer_create(self):
        self.assertEqual(self.named, models.Timer.objects.get(name='Named'))
        self.assertEqual(str(self.named), 'Named')
        self.assertEqual(self.unnamed, models.Timer.objects.get(name=None))
        self.assertEqual(
            str(self.unnamed), 'Timer #{}'.format(self.unnamed.id))

    def test_timer_title_with_child(self):
        self.assertEqual(self.named.title_with_child, str(self.named))

        models.Child.objects.create(
            first_name='Child',
            last_name='Two',
            birth_date=timezone.localdate()
        )
        self.assertEqual(
            self.named.title_with_child,
            '{} ({})'.format(str(self.named), str(self.named.child))
        )

    def test_timer_user_username(self):
        self.assertEqual(self.named.user_username, self.user.get_username())
        self.user.first_name = 'User'
        self.user.last_name = 'Name'
        self.user.save()
        self.assertEqual(self.named.user_username, self.user.get_full_name())

    def test_timer_restart(self):
        self.named.restart()
        self.assertIsNone(self.named.end)
        self.assertIsNone(self.named.duration)
        self.assertTrue(self.named.active)

    def test_timer_stop(self):
        stop_time = timezone.localtime()
        self.unnamed.stop(end=stop_time)
        self.assertEqual(self.unnamed.end, stop_time)
        self.assertEqual(
            self.unnamed.duration.seconds,
            (self.unnamed.end - self.unnamed.start).seconds)
        self.assertFalse(self.unnamed.active)

    def test_timer_duration(self):
        timer = models.Timer.objects.create(user=User.objects.first())
        # Timer.start uses auto_now_add, so it cannot be set in create().
        timer.start = timezone.localtime() - timezone.timedelta(minutes=30)
        timer.save()
        timer.refresh_from_db()

        self.assertEqual(
            timer.duration.seconds,
            timezone.timedelta(minutes=30).seconds)
        timer.stop()
        self.assertEqual(
            timer.duration.seconds,
            timezone.timedelta(minutes=30).seconds)


class TummyTimeTestCase(TestCase):
    def setUp(self):
        call_command('migrate', verbosity=0)
        self.child = models.Child.objects.create(
            first_name='First',
            last_name='Last',
            birth_date=timezone.localdate()
        )

    def test_tummytime_create(self):
        tummy_time = models.TummyTime.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
        )
        self.assertEqual(tummy_time, models.TummyTime.objects.first())
        self.assertEqual(str(tummy_time), 'Tummy Time')
        self.assertEqual(
            tummy_time.duration, tummy_time.end - tummy_time.start)
