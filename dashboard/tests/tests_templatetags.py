# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
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
        cls.context = {"request": MockUserRequest(get_user_model().objects.first())}

        # Ensure timezone matches the one defined by fixtures.
        user_timezone = Settings.objects.first().timezone
        timezone.activate(user_timezone)

        # Test file data uses a basis date of 2017-11-18.
        date = timezone.localtime().strptime("2017-11-18", "%Y-%m-%d")
        cls.date = timezone.make_aware(date)

    def test_hide_empty(self):
        request = MockUserRequest(get_user_model().objects.first())
        request.user.settings.dashboard_hide_empty = True
        context = {"request": request}
        hide_empty = cards._hide_empty(context)
        self.assertTrue(hide_empty)

    def test_filter_data_age_none(self):
        request = MockUserRequest(get_user_model().objects.first())
        request.user.settings.dashboard_hide_age = None
        context = {"request": request}
        filter_data_age = cards._filter_data_age(context)
        self.assertFalse(len(filter_data_age))

    @mock.patch("dashboard.templatetags.cards.timezone")
    def test_filter_data_age_one_day(self, mocked_timezone):
        request = MockUserRequest(get_user_model().objects.first())
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
        request = MockUserRequest(get_user_model().objects.first())
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
            0: {
                "wet_pct": 50.0,
                "solid_pct": 50.0,
                "empty_pct": 0.0,
                "solid": 1,
                "wet": 1,
                "empty": 0.0,
                "changes": 2.0,
            },
            1: {
                "wet_pct": 0.0,
                "solid_pct": 100.0,
                "empty_pct": 0.0,
                "solid": 2,
                "wet": 0,
                "empty": 0.0,
                "changes": 2.0,
            },
            2: {
                "wet_pct": 100.0,
                "solid_pct": 0.0,
                "empty_pct": 0.0,
                "solid": 0,
                "wet": 2,
                "empty": 0.0,
                "changes": 2.0,
            },
            3: {
                "wet_pct": 75.0,
                "solid_pct": 25.0,
                "empty_pct": 0.0,
                "solid": 1,
                "wet": 3,
                "empty": 0.0,
                "changes": 4.0,
            },
            4: {
                "wet_pct": 100.0,
                "solid_pct": 0.0,
                "empty_pct": 0.0,
                "solid": 0,
                "wet": 1,
                "empty": 0.0,
                "changes": 1.0,
            },
            5: {
                "wet_pct": 100.0,
                "solid_pct": 0.0,
                "empty_pct": 0.0,
                "solid": 0,
                "wet": 2,
                "empty": 0.0,
                "changes": 2.0,
            },
            6: {
                "wet_pct": 100.0,
                "solid_pct": 0.0,
                "empty_pct": 0.0,
                "solid": 0,
                "wet": 1,
                "empty": 0.0,
                "changes": 1.0,
            },
        }
        self.assertEqual(data["stats"], stats)

    def test_card_feeding_recent(self):
        data = cards.card_feeding_recent(self.context, self.child, self.date)

        self.assertEqual(data["type"], "feeding")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])

        # most recent day
        self.assertEqual(data["feedings"][0]["total"], 2.5)
        self.assertEqual(data["feedings"][0]["count"], 3)

        # yesterday
        self.assertEqual(data["feedings"][1]["total"], 0.25)
        self.assertEqual(data["feedings"][1]["count"], 1)

        # last day
        self.assertEqual(data["feedings"][-1]["total"], 20.0)
        self.assertEqual(data["feedings"][-1]["count"], 2)

    def test_card_feeding_last(self):
        data = cards.card_feeding_last(self.context, self.child)
        self.assertEqual(data["type"], "feeding")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertIsInstance(data["feeding"], models.Feeding)
        self.assertEqual(data["feeding"], models.Feeding.objects.first())
        self.assertEqual(
            data["feeding_diff_base"], models.Feeding.objects.first().start
        )

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

    def test_card_pumping_last(self):
        data = cards.card_pumping_last(self.context, self.child)
        self.assertEqual(data["type"], "pumping")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertIsInstance(data["pumping"], models.Pumping)
        self.assertEqual(data["pumping"], models.Pumping.objects.first())

    def test_card_pumping_recent(self):
        data = cards.card_pumping_recent(self.context, self.child, self.date)
        self.assertEqual(data["type"], "pumping")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])

        # 8 days of data returned
        self.assertEqual(len(data["pumpings"]), 8)

        # Fixture has 2 pumpings on 2017-11-17 (amounts 5.0 and 9.0).
        # self.date is 2017-11-18, so 2017-11-17 is index 1 (yesterday).
        self.assertEqual(data["pumpings"][1]["total"], 14.0)
        self.assertEqual(data["pumpings"][1]["count"], 2)

        # Today (2017-11-18) should have no pumpings.
        self.assertEqual(data["pumpings"][0]["total"], 0)
        self.assertEqual(data["pumpings"][0]["count"], 0)

    def test_card_pumping_recent_empty(self):
        models.Pumping.objects.all().delete()
        data = cards.card_pumping_recent(self.context, self.child, self.date)
        self.assertEqual(data["type"], "pumping")
        self.assertTrue(data["empty"])
        self.assertFalse(data["hide_empty"])

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
        data = cards.card_sleep_recent(self.context, self.child, self.date)
        self.assertEqual(data["type"], "sleep")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertEqual(data["sleeps"][0]["total"], timezone.timedelta(seconds=43200))
        self.assertEqual(data["sleeps"][0]["count"], 3)

        self.assertEqual(data["sleeps"][1]["total"], timezone.timedelta(seconds=30600))
        self.assertEqual(data["sleeps"][1]["count"], 1)

    def test_card_sleep_naps_day(self):
        data = cards.card_sleep_naps_day(self.context, self.child, self.date)
        self.assertEqual(data["type"], "sleep")
        self.assertFalse(data["empty"])
        self.assertFalse(data["hide_empty"])
        self.assertEqual(data["total"], timezone.timedelta(0, 7200))
        self.assertEqual(data["count"], 1)

    def test_card_statistics(self):
        data = cards.card_statistics(self.context, self.child)
        stats = [
            # Statistics date basis is not particularly strong to these diaper change
            # examples.
            # TODO: Improve testing of diaper change frequency statistics.
            {
                "type": "duration",
                "stat": 0.0,
                "title": "Diaper change frequency (past 3 days)",
            },
            {
                "type": "duration",
                "stat": 0.0,
                "title": "Diaper change frequency (past 2 weeks)",
            },
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
                "stat": timezone.timedelta(days=1, seconds=39780),
                "title": "Feeding frequency",
            },
            {
                "title": "Average nap duration",
                "stat": timezone.timedelta(0, 6300),
                "type": "duration",
            },
            {"title": "Average naps per day", "stat": 1.0, "type": "float"},
            {
                "title": "Average sleep duration",
                "stat": timezone.timedelta(0, 19800),
                "type": "duration",
            },
            {
                "title": "Average awake duration",
                "stat": timezone.timedelta(0, 18000),
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
        user = get_user_model().objects.first()
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
        self.assertEqual(len(data["instances"]), 4)

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

    def test_card_breast_activity_pumping_only(self):
        # No breast feedings — card must show pumping as the latest activity.
        models.Feeding.objects.filter(
            method__in=["left breast", "right breast", "both breasts"]
        ).delete()
        data = cards.card_breast_activity(self.context, self.child)
        self.assertEqual(data["latest_type"], "pumping")
        self.assertEqual(data["type"], "pumping")
        self.assertFalse(data["empty"])
        self.assertIsInstance(data["latest"], models.Pumping)
        self.assertIsNone(data["feeding"])
        self.assertIsNotNone(data["pumping"])

    def test_card_breast_activity_feeding_only(self):
        # No pumpings — card must show breastfeeding as the latest activity.
        models.Pumping.objects.all().delete()
        data = cards.card_breast_activity(self.context, self.child)
        self.assertEqual(data["latest_type"], "feeding")
        self.assertEqual(data["type"], "feeding")
        self.assertFalse(data["empty"])
        self.assertIsInstance(data["latest"], models.Feeding)
        self.assertIsNotNone(data["feeding"])
        self.assertIsNone(data["pumping"])

    def test_card_breast_activity_pumping_more_recent(self):
        # Add a pumping after the last breast feeding — pumping must win.
        models.Pumping.objects.create(
            child=self.child,
            start=timezone.make_aware(
                timezone.localtime().strptime("2017-11-18 12:30", "%Y-%m-%d %H:%M")
            ),
            end=timezone.make_aware(
                timezone.localtime().strptime("2017-11-18 12:45", "%Y-%m-%d %H:%M")
            ),
            amount=6.0,
            amount_unit="oz",
        )
        data = cards.card_breast_activity(self.context, self.child)
        self.assertEqual(data["latest_type"], "pumping")
        self.assertEqual(data["type"], "pumping")
        self.assertIsInstance(data["latest"], models.Pumping)
        # Both branches still carry data for the footer.
        self.assertIsNotNone(data["feeding"])
        self.assertIsNotNone(data["pumping"])

    def test_card_breast_activity_feeding_more_recent(self):
        # Fixture default: breast feeding (Nov 18 12:00) is newer than
        # last pumping (Nov 17 20:22) — feeding must win.
        data = cards.card_breast_activity(self.context, self.child)
        self.assertEqual(data["latest_type"], "feeding")
        self.assertEqual(data["type"], "feeding")
        self.assertIsInstance(data["latest"], models.Feeding)
        self.assertIsNotNone(data["feeding"])
        self.assertIsNotNone(data["pumping"])

    # ── breast_activity_time_mode setting tests ──

    def test_card_breast_activity_time_mode_default_end(self):
        """Default time_mode should be 'end' (backward compatible)."""
        data = cards.card_breast_activity(self.context, self.child)
        self.assertEqual(data["time_mode"], "end")

    def test_card_breast_activity_time_mode_start(self):
        """When setting is 'start', compare by start times."""
        user = get_user_model().objects.first()
        user.settings.breast_activity_time_mode = "start"
        user.settings.save()
        context = {"request": MockUserRequest(user)}
        data = cards.card_breast_activity(context, self.child)
        self.assertEqual(data["time_mode"], "start")

    def test_card_breast_activity_start_mode_changes_winner(self):
        """In 'start' mode, the activity that STARTED more recently wins.

        Scenario: feeding ends later but pumping starts later.
        With END mode: feeding wins (it ends later).
        With START mode: pumping wins (it starts later).
        """
        # Clean slate
        models.Feeding.objects.all().delete()
        models.Pumping.objects.all().delete()

        # Feeding: starts early, ends late
        models.Feeding.objects.create(
            child=self.child,
            start=timezone.make_aware(
                timezone.localtime().strptime("2017-11-18 10:00", "%Y-%m-%d %H:%M")
            ),
            end=timezone.make_aware(
                timezone.localtime().strptime("2017-11-18 11:00", "%Y-%m-%d %H:%M")
            ),
            method="left breast",
        )
        # Pumping: starts later, ends earlier
        models.Pumping.objects.create(
            child=self.child,
            start=timezone.make_aware(
                timezone.localtime().strptime("2017-11-18 10:30", "%Y-%m-%d %H:%M")
            ),
            end=timezone.make_aware(
                timezone.localtime().strptime("2017-11-18 10:40", "%Y-%m-%d %H:%M")
            ),
            amount=4.0,
            amount_unit="oz",
        )

        # END mode: feeding wins (ends at 11:00 > pumping 10:40)
        user = get_user_model().objects.first()
        user.settings.breast_activity_time_mode = "end"
        user.settings.save()
        context = {"request": MockUserRequest(user)}
        data = cards.card_breast_activity(context, self.child)
        self.assertEqual(data["time_mode"], "end")
        self.assertEqual(data["latest_type"], "feeding")

        # START mode: pumping wins (starts at 10:30 > feeding 10:00)
        user.settings.breast_activity_time_mode = "start"
        user.settings.save()
        context = {"request": MockUserRequest(user)}
        data = cards.card_breast_activity(context, self.child)
        self.assertEqual(data["time_mode"], "start")
        self.assertEqual(data["latest_type"], "pumping")
