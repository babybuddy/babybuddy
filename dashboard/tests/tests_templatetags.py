# -*- coding: utf-8 -*-
import pytz

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from babybuddy.models import Settings
from core import models
from dashboard.templatetags import cards


class TemplateTagsTestCase(TestCase):
    fixtures = ['tests.json']

    @classmethod
    def setUpClass(cls):
        super(TemplateTagsTestCase, cls).setUpClass()
        cls.child = models.Child.objects.first()

        # Ensure timezone matches the one defined by fixtures.
        user_timezone = Settings.objects.first().timezone
        timezone.activate(pytz.timezone(user_timezone))

        # Test file data uses a basis date of 2017-11-18.
        date = timezone.localtime().strptime('2017-11-18', '%Y-%m-%d')
        cls.date = timezone.make_aware(date)

    def test_card_diaperchange_last(self):
        data = cards.card_diaperchange_last(self.child)
        self.assertEqual(data['type'], 'diaperchange')
        self.assertIsInstance(data['change'], models.DiaperChange)
        self.assertEqual(data['change'], models.DiaperChange.objects.first())

    def test_card_diaperchange_types(self):
        data = cards.card_diaperchange_types(self.child, self.date)
        self.assertEqual(data['type'], 'diaperchange')
        stats = {
            0: {'wet_pct': 50.0, 'solid_pct': 50.0, 'solid': 1, 'wet': 1},
            1: {'wet_pct': 0.0, 'solid_pct': 100.0, 'solid': 2, 'wet': 0},
            2: {'wet_pct': 100.0, 'solid_pct': 0.0, 'solid': 0, 'wet': 2},
            3: {'wet_pct': 75.0, 'solid_pct': 25.0, 'solid': 1, 'wet': 3},
            4: {'wet_pct': 100.0, 'solid_pct': 0.0, 'solid': 0, 'wet': 1},
            5: {'wet_pct': 100.0, 'solid_pct': 0.0, 'solid': 0, 'wet': 2},
            6: {'wet_pct': 100.0, 'solid_pct': 0.0, 'solid': 0, 'wet': 1}
        }
        self.assertEqual(data['stats'], stats)

    def test_card_feeding_day(self):
        data = cards.card_feeding_day(self.child, self.date)
        self.assertEqual(data['type'], 'feeding')
        self.assertEqual(data['total'], 2.5)
        self.assertEqual(data['count'], 3)

    def test_card_feeding_last(self):
        data = cards.card_feeding_last(self.child)
        self.assertEqual(data['type'], 'feeding')
        self.assertIsInstance(data['feeding'], models.Feeding)
        self.assertEqual(data['feeding'], models.Feeding.objects.first())

    def test_card_feeding_last_method(self):
        data = cards.card_feeding_last_method(self.child)
        self.assertEqual(data['type'], 'feeding')
        self.assertEqual(len(data['feedings']), 3)
        for feeding in data['feedings']:
            self.assertIsInstance(feeding, models.Feeding)
        self.assertEqual(
            data['feedings'][2].method,
            models.Feeding.objects.first().method)

    def test_card_sleep_last(self):
        data = cards.card_sleep_last(self.child)
        self.assertEqual(data['type'], 'sleep')
        self.assertIsInstance(data['sleep'], models.Sleep)
        self.assertEqual(data['sleep'], models.Sleep.objects.first())

    def test_card_sleep_day(self):
        data = cards.card_sleep_day(self.child, self.date)
        self.assertEqual(data['type'], 'sleep')
        self.assertEqual(data['total'], timezone.timedelta(2, 7200))
        self.assertEqual(data['count'], 4)

    def test_card_sleep_naps_day(self):
        data = cards.card_sleep_naps_day(self.child, self.date)
        self.assertEqual(data['type'], 'sleep')
        self.assertEqual(data['total'], timezone.timedelta(0, 9000))
        self.assertEqual(data['count'], 2)

    def test_card_statistics(self):
        data = cards.card_statistics(self.child)
        stats = [
            {
                'title': 'Diaper change frequency',
                'stat': timezone.timedelta(0, 44228, 571429),
                'type': 'duration'
            },
            # Statistics date basis is not particularly strong to these feeding
            # examples.
            # TODO: Improve testing of feeding frequency statistics.
            {
                'type': 'duration',
                'stat': 0.0,
                'title': 'Feeding frequency (past 3 days)'
            },
            {
                'type': 'duration',
                'stat': 0.0,
                'title': 'Feeding frequency (past 2 weeks)'},
            {
                'type': 'duration',
                'stat': timezone.timedelta(0, 7200),
                'title': 'Feeding frequency'
            },
            {
                'title': 'Average nap duration',
                'stat': timezone.timedelta(0, 4500),
                'type': 'duration'
            },
            {
                'title': 'Average naps per day',
                'stat': 2.0,
                'type': 'float'
            },
            {
                'title': 'Average sleep duration',
                'stat': timezone.timedelta(0, 6750),
                'type': 'duration'
            },
            {
                'title': 'Average awake duration',
                'stat': timezone.timedelta(0, 19200),
                'type': 'duration'
            },
            {
                'title': 'Weight change per week',
                'stat': 1.0, 'type':
                'float'
            }
        ]

        self.assertEqual(data['stats'], stats)

    def test_card_timer_list(self):
        user = User.objects.first()
        child = models.Child.objects.first()
        child_two = models.Child.objects.create(
            first_name='Child',
            last_name='Two',
            birth_date=timezone.localdate()
        )
        timers = {
            'no_child': models.Timer.objects.create(
                user=user,
                start=timezone.localtime() - timezone.timedelta(hours=3)
            ),
            'child': models.Timer.objects.create(
                user=user,
                child=child,
                start=timezone.localtime() - timezone.timedelta(hours=2)
            ),
            'child_two': models.Timer.objects.create(
                user=user,
                child=child_two,
                start=timezone.localtime() - timezone.timedelta(hours=1)
            ),
        }

        data = cards.card_timer_list()
        self.assertIsInstance(data['instances'][0], models.Timer)
        self.assertEqual(len(data['instances']), 3)

        data = cards.card_timer_list(child)
        self.assertIsInstance(data['instances'][0], models.Timer)
        self.assertTrue(timers['no_child'] in data['instances'])
        self.assertTrue(timers['child'] in data['instances'])
        self.assertFalse(timers['child_two'] in data['instances'])

        data = cards.card_timer_list(child_two)
        self.assertIsInstance(data['instances'][0], models.Timer)
        self.assertTrue(timers['no_child'] in data['instances'])
        self.assertTrue(timers['child_two'] in data['instances'])
        self.assertFalse(timers['child'] in data['instances'])

    def test_card_tummytime_last(self):
        data = cards.card_tummytime_last(self.child)
        self.assertEqual(data['type'], 'tummytime')
        self.assertIsInstance(data['tummytime'], models.TummyTime)
        self.assertEqual(data['tummytime'], models.TummyTime.objects.first())

    def test_card_tummytime_day(self):
        data = cards.card_tummytime_day(self.child, self.date)
        self.assertEqual(data['type'], 'tummytime')
        self.assertIsInstance(data['instances'].first(), models.TummyTime)
        self.assertIsInstance(data['last'], models.TummyTime)
        stats = {'count': 3, 'total': timezone.timedelta(0, 300)}
        self.assertEqual(data['stats'], stats)
