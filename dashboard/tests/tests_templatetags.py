# -*- coding: utf-8 -*-
import pytz

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from babybuddy.models import Settings
from core import models
from dashboard.templatetags import cards

from unittest import mock


class MockUserRequest:
    def __init__(self, user):
        self.user = user


class TemplateTagsTestCase(TestCase):
    fixtures = ["tests.json"]

    @classmethod
    def setUpClass(cls):
        super(TemplateTagsTestCase, cls).setUpClass()
        cls.child = models.Child.objects.first()
        cls.context = {"request": MockUserRequest(User.objects.first())}

        # Ensure timezone matches the one defined by fixtures.
        user_timezone = Settings.objects.first().timezone
        timezone.activate(pytz.timezone(user_timezone))

        # Test file data uses a basis date of 2017-11-18.
        date = timezone.localtime().strptime("2017-11-18", "%Y-%m-%d")
        cls.date = timezone.make_aware(date)

    def test_hide_empty(self):
        request = MockUserRequest(User.objects.first())
        request.user.settings.dashboard_hide_empty = True
        context = {"request": request}
        hide_empty = cards._hide_empty(context)
        self.assertTrue(hide_empty)

    def test_filter_data_age_none(self):
        request = MockUserRequest(User.objects.first())
        request.user.settings.dashboard_hide_age = None
        context = {"request": request}
        filter_data_age = cards._filter_data_age(context)
        self.assertFalse(len(filter_data_age))

    @mock.patch("dashboard.templatetags.cards.timezone")
    def test_filter_data_age_one_day(self, mocked_timezone):
        request = MockUserRequest(User.objects.first())
        request.user.settings.dashboard_hide_age = timezone.timedelta(days=1)
        context = {"request": request}
        mocked_timezone.localtime.return_value = timezone.localtime().strptime(
            "2017-11-18", "%Y-%m-%d"
        )

        filter_data_age = cards._filter_data_age(context, keyword="time")

        self.assertIn("time__range", filter_data_age)
        self.assertEqual(
            filter_data_age["time__range"][0],
            timezone.localtime().strptime("2017-11-17", "%Y-%m-%d"),
        )
        self.assertEqual(
            filter_data_age["time__range"][1],
            timezone.localtime().strptime("2017-11-18", "%Y-%m-%d"),
        )

    def test_card_diaperchange_last(self):
        data = cards.card_diaperchange_last(self.context, self.child)
        self.assertEqual(data["type"], "diaperchange")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertIsInstance(data["change"], models.DiaperChange)
        self.assertEqual(data["change"], models.DiaperChange.objects.first())

    @mock.patch("dashboard.templatetags.cards.timezone")
    def test_card_diaperchange_last_filter_age(self, mocked_timezone):
        request = MockUserRequest(User.objects.first())
        request.user.settings.dashboard_hide_age = timezone.timedelta(days=1)
        context = {"request": request}
        time = timezone.localtime().strptime("2017-11-10", "%Y-%m-%d")
        mocked_timezone.localtime.return_value = timezone.make_aware(time)

        data = cards.card_diaperchange_last(context, self.child)
        self.assertTrue(data["empty"])

    def test_card_diaperchange_types(self):
        data = cards.card_diaperchange_types(self.context, self.child, self.date)
        self.assertEqual(data["type"], "diaperchange")
        stats = {
            0: {"wet_pct": 50.0, "solid_pct": 50.0, "solid": 1, "wet": 1},
            1: {"wet_pct": 0.0, "solid_pct": 100.0, "solid": 2, "wet": 0},
            2: {"wet_pct": 100.0, "solid_pct": 0.0, "solid": 0, "wet": 2},
            3: {"wet_pct": 75.0, "solid_pct": 25.0, "solid": 1, "wet": 3},
            4: {"wet_pct": 100.0, "solid_pct": 0.0, "solid": 0, "wet": 1},
            5: {"wet_pct": 100.0, "solid_pct": 0.0, "solid": 0, "wet": 2},
            6: {"wet_pct": 100.0, "solid_pct": 0.0, "solid": 0, "wet": 1},
        }
        self.assertEqual(data["stats"], stats)

    def test_card_feeding_day(self):
        data = cards.card_feeding_day(self.context, self.child, self.date)
        self.assertEqual(data["type"], "feeding")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertEqual(data["total"], 2.5)
        self.assertEqual(data["count"], 3)

    def test_card_feeding_last(self):
        data = cards.card_feeding_last(self.context, self.child)
        self.assertEqual(data["type"], "feeding")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertIsInstance(data["feeding"], models.Feeding)
        self.assertEqual(data["feeding"], models.Feeding.objects.first())

    def test_card_feeding_last_method(self):
        data = cards.card_feeding_last_method(self.context, self.child)
        self.assertEqual(data["type"], "feeding")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertEqual(len(data["feedings"]), 3)
        for feeding in data["feedings"]:
            self.assertIsInstance(feeding, models.Feeding)
        self.assertEqual(
            data["feedings"][2].method, models.Feeding.objects.first().method
        )

    def test_card_sleep_last(self):
        data = cards.card_sleep_last(self.context, self.child)
        self.assertEqual(data["type"], "sleep")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertIsInstance(data["sleep"], models.Sleep)
        self.assertEqual(data["sleep"], models.Sleep.objects.first())

    def test_card_sleep_last_empty(self):
        models.Sleep.objects.all().delete()
        data = cards.card_sleep_last(self.context, self.child)
        self.assertEqual(data["type"], "sleep")
        self.assertTrue(data["empty"])
        self.assertFalse(data["hide_empty"])

    def test_card_sleep_day(self):
        data = cards.card_sleep_day(self.context, self.child, self.date)
        self.assertEqual(data["type"], "sleep")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertEqual(data["total"], timezone.timedelta(2, 7200))
        self.assertEqual(data["count"], 4)

    def test_card_sleep_naps_day(self):
        data = cards.card_sleep_naps_day(self.context, self.child, self.date)
        self.assertEqual(data["type"], "sleep")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertEqual(data["total"], timezone.timedelta(0, 9000))
        self.assertEqual(data["count"], 2)

    def test_card_statistics(self):
        data = cards.card_statistics(self.context, self.child)
        stats = [
            {
                "title": "Diaper change frequency",
                "stat": timezone.timedelta(0, 44228, 571429),
                "type": "duration",
            },
            # Statistics date basis is not particularly strong to these feeding
            # examples.
            # TODO: Improve testing of feeding frequency statistics.
            {
                "type": "duration",
                "stat": 0.0,
                "title": "Feeding frequency (past 3 days)",
            },
            {
                "type": "duration",
                "stat": 0.0,
                "title": "Feeding frequency (past 2 weeks)",
            },
            {
                "type": "duration",
                "stat": timezone.timedelta(0, 7200),
                "title": "Feeding frequency",
            },
            {
                "title": "Average nap duration",
                "stat": timezone.timedelta(0, 4500),
                "type": "duration",
            },
            {"title": "Average naps per day", "stat": 2.0, "type": "float"},
            {
                "title": "Average sleep duration",
                "stat": timezone.timedelta(0, 6750),
                "type": "duration",
            },
            {
                "title": "Average awake duration",
                "stat": timezone.timedelta(0, 19200),
                "type": "duration",
            },
            {"title": "Weight change per week", "stat": 1.0, "type": "float"},
            {"title": "Height change per week", "stat": 1.0, "type": "float"},
            {
                "title": "Head circumference change per week",
                "stat": 1.0,
                "type": "float",
            },
            {"title": "BMI change per week", "stat": 1.0, "type": "float"},
        ]

        self.assertEqual(data["stats"], stats)
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])

    def test_card_timer_list(self):
        user = User.objects.first()
        child = models.Child.objects.first()
        child_two = models.Child.objects.create(
            first_name="Child", last_name="Two", birth_date=timezone.localdate()
        )
        timers = {
            "no_child": models.Timer.objects.create(
                user=user, start=timezone.localtime() - timezone.timedelta(hours=3)
            ),
            "child": models.Timer.objects.create(
                user=user,
                child=child,
                start=timezone.localtime() - timezone.timedelta(hours=2),
            ),
            "child_two": models.Timer.objects.create(
                user=user,
                child=child_two,
                start=timezone.localtime() - timezone.timedelta(hours=1),
            ),
        }

        data = cards.card_timer_list(self.context)
        self.assertIsInstance(data["instances"][0], models.Timer)
        self.assertEqual(len(data["instances"]), 3)

        data = cards.card_timer_list(self.context, child)
        self.assertIsInstance(data["instances"][0], models.Timer)
        self.assertTrue(timers["no_child"] in data["instances"])
        self.assertTrue(timers["child"] in data["instances"])
        self.assertFalse(timers["child_two"] in data["instances"])

        data = cards.card_timer_list(self.context, child_two)
        self.assertIsInstance(data["instances"][0], models.Timer)
        self.assertTrue(timers["no_child"] in data["instances"])
        self.assertTrue(timers["child_two"] in data["instances"])
        self.assertFalse(timers["child"] in data["instances"])

    def test_card_tummytime_last(self):
        data = cards.card_tummytime_last(self.context, self.child)
        self.assertEqual(data["type"], "tummytime")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertIsInstance(data["tummytime"], models.TummyTime)
        self.assertEqual(data["tummytime"], models.TummyTime.objects.first())

    def test_card_tummytime_day(self):
        data = cards.card_tummytime_day(self.context, self.child, self.date)
        self.assertEqual(data["type"], "tummytime")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertIsInstance(data["instances"].first(), models.TummyTime)
        self.assertIsInstance(data["last"], models.TummyTime)
        stats = {"count": 3, "total": timezone.timedelta(0, 300)}
        self.assertEqual(data["stats"], stats)
