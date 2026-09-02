# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone, formats

from core.models import Child, Timer
from core.templatetags import bootstrap, datetime as datetime_tags, duration, timers
from core.templatetags.time_filters import hour_format, datetime_format
from babybuddy.models import Settings


class MockUserRequest:
    def __init__(self, user):
        self.user = user


class TemplateTagsTestCase(TestCase):
    def test_bootstrap_bool_icon(self):
        self.assertEqual(
            bootstrap.bool_icon(True),
            '<i class="icon-true text-success" aria-hidden="true"></i>',
        )
        self.assertEqual(
            bootstrap.bool_icon(False),
            '<i class="icon-false text-danger" aria-hidden="true"></i>',
        )

    # def test_child_age_string(self):
    #     self.assertEqual(
    #         "6\xa0hours",
    #         duration.child_age_string(
    #             timezone.localtime() - timezone.timedelta(days=0, hours=6)
    #         ),
    #     )
    #     self.assertEqual(
    #         "1\xa0day",
    #         duration.child_age_string(
    #             timezone.localdate() - timezone.timedelta(days=1, hours=6)
    #         ),
    #     )
    #     self.assertEqual(
    #         "1\xa0month",
    #         duration.child_age_string(
    #             timezone.localdate() - timezone.timedelta(days=45)
    #         ),
    #     )
    #     self.assertEqual(
    #         "3\xa0months",
    #         duration.child_age_string(
    #             timezone.localdate() - timezone.timedelta(days=95)
    #         ),
    #     )
    #     self.assertEqual("", duration.child_age_string(None))
    #     self.assertEqual("", duration.child_age_string("not a date!!"))

    def test_duration_duration_string(self):
        delta = timezone.timedelta(hours=1, minutes=30, seconds=15)
        self.assertEqual(
            duration.duration_string(delta), "1 hour, 30 minutes, 15 seconds"
        )
        self.assertEqual(duration.duration_string(delta, "m"), "1 hour, 30 minutes")
        self.assertEqual(duration.duration_string(delta, "h"), "1 hour")

        self.assertEqual(duration.duration_string(""), "")
        self.assertRaises(TypeError, duration.duration_string("not a delta"))

    def test_duration_hours(self):
        delta = timezone.timedelta(hours=1)
        self.assertEqual(duration.hours(delta), 1)
        self.assertEqual(duration.hours(""), 0)
        self.assertRaises(TypeError, duration.hours("not a delta"))

    def test_duration_minutes(self):
        delta = timezone.timedelta(minutes=45)
        self.assertEqual(duration.minutes(delta), 45)
        self.assertEqual(duration.minutes(""), 0)
        self.assertRaises(TypeError, duration.minutes("not a delta"))

    def test_duration_seconds(self):
        delta = timezone.timedelta(seconds=20)
        self.assertEqual(duration.seconds(delta), 20)
        self.assertEqual(duration.seconds(""), 0)
        self.assertRaises(TypeError, duration.seconds("not a delta"))

    def test_duration_dayssince(self):
        # test with a few different dates that could be pathological
        dates = [
            timezone.datetime(2022, 1, 1, 0, 0, 1).date(),  # new year
            timezone.datetime(2021, 12, 31, 23, 59, 59).date(),  # almost new year
            timezone.datetime(
                1969, 2, 1, 23, 59, 59
            ).date(),  # old but middle of the year
        ]
        for d in dates:
            self.assertEqual(duration.dayssince(d, today=d), "today")
            self.assertEqual(
                duration.dayssince((d - timezone.timedelta(hours=5)), today=d), "today"
            )
            self.assertEqual(
                duration.dayssince((d - timezone.timedelta(hours=24)), today=d),
                "yesterday",
            )
            self.assertEqual(
                duration.dayssince((d - timezone.timedelta(hours=24 * 2)), today=d),
                "2 days ago",
            )
            self.assertEqual(
                duration.dayssince((d - timezone.timedelta(hours=24 * 10)), today=d),
                "10 days ago",
            )
            self.assertEqual(
                duration.dayssince((d - timezone.timedelta(hours=24 * 60)), today=d),
                "60 days ago",
            )

    def test_duration_deltasince(self):
        datetimes = [
            (
                timezone.datetime(2022, 1, 1, 0, 0, 1),
                timezone.timedelta(seconds=1),
            ),  # new year
            (
                timezone.datetime(2021, 12, 31, 23, 59, 59),
                timezone.timedelta(seconds=3),
            ),  # almost new year
            (
                timezone.datetime(1969, 2, 1, 23, 59, 59),
                timezone.timedelta(days=19326, seconds=3),
            ),  # old but middle of the year
        ]
        now = timezone.datetime(2022, 1, 1, 0, 0, 2)
        for d, expected_delta in datetimes:
            with self.subTest():
                self.assertEqual(duration.deltasince(d, now), expected_delta)

    def test_instance_add_url(self):
        child = Child.objects.create(
            first_name="Test", last_name="Child", birth_date=timezone.localdate()
        )
        user = get_user_model().objects.create_user(username="timer")
        timer = Timer.objects.create(user=user)

        url = timers.instance_add_url({"timer": timer}, "core:sleep-add")
        self.assertEqual(url, "/sleep/add/?timer={}".format(timer.id))

        timer = Timer.objects.create(user=user, child=child)
        url = timers.instance_add_url({"timer": timer}, "core:sleep-add")
        self.assertEqual(
            url, "/sleep/add/?timer={}&child={}".format(timer.id, child.slug)
        )

    def test_datetime_short(self):
        date = timezone.localtime()
        self.assertEqual(
            datetime_tags.datetime_short(date),
            "Today, {}".format(formats.date_format(date, format="TIME_FORMAT")),
        )

        date = timezone.localtime() - timezone.timedelta(days=1, hours=6)
        self.assertEqual(
            datetime_tags.datetime_short(date),
            "{}, {}".format(
                formats.date_format(date, format="SHORT_MONTH_DAY_FORMAT"),
                formats.date_format(date, format="TIME_FORMAT"),
            ),
        )


class HourFormatFilterTestCase(TestCase):
    """Tests for hour_format and datetime_format template filters."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testfilteruser", password="password"
        )
        self.settings = self.user.settings
        self.settings.hour_format = False
        self.settings.save()

        # A fixed aware datetime: 2026-08-11 21:23:00 UTC
        self.aware_dt = timezone.datetime(
            2026, 8, 11, 21, 23, 0, tzinfo=datetime.timezone.utc
        )
        # A plain time object
        self.plain_time = datetime.time(21, 23)
        # A plain date object
        self.plain_date = datetime.date(2026, 8, 11)

    # ------------------------------------------------------------------
    # hour_format — 12-hour mode (default)
    # ------------------------------------------------------------------

    def test_hour_format_12h_datetime(self):
        """With 24h off, aware datetime is formatted using Django TIME_FORMAT."""
        result = hour_format(self.aware_dt)
        local = timezone.localtime(self.aware_dt)
        expected = formats.time_format(local, "TIME_FORMAT")
        self.assertEqual(result, expected)

    def test_hour_format_12h_time(self):
        """With 24h off, a plain time object is formatted using Django TIME_FORMAT."""
        result = hour_format(self.plain_time)
        expected = formats.time_format(self.plain_time, "TIME_FORMAT")
        self.assertEqual(result, expected)

    def test_hour_format_12h_none(self):
        self.assertEqual(hour_format(None), "")

    def test_hour_format_12h_plain_date_returns_empty(self):
        """A bare date (no time) should return empty string."""
        self.assertEqual(hour_format(self.plain_date), "")

    # ------------------------------------------------------------------
    # hour_format — 24-hour mode
    # ------------------------------------------------------------------

    def test_hour_format_24h_datetime(self):
        """With 24h on, aware datetime is formatted as HH:MM."""
        self.settings.hour_format = True
        self.settings.save()

        local = timezone.localtime(self.aware_dt)
        result = hour_format(self.aware_dt)
        expected = local.strftime("%H:%M")
        self.assertEqual(result, expected)
        # Must not contain am/pm markers
        self.assertNotIn("a.m.", result)
        self.assertNotIn("p.m.", result)
        self.assertNotIn("AM", result)
        self.assertNotIn("PM", result)

    def test_hour_format_24h_time(self):
        """With 24h on, a plain time is formatted as HH:MM."""
        self.settings.hour_format = True
        self.settings.save()

        result = hour_format(self.plain_time)
        self.assertEqual(result, "21:23")

    def test_hour_format_24h_midnight(self):
        """Midnight should render as 00:00 in 24h mode."""
        self.settings.hour_format = True
        self.settings.save()

        midnight = datetime.time(0, 0)
        self.assertEqual(hour_format(midnight), "00:00")

    def test_hour_format_24h_noon(self):
        """Noon should render as 12:00 in 24h mode."""
        self.settings.hour_format = True
        self.settings.save()

        noon = datetime.time(12, 0)
        self.assertEqual(hour_format(noon), "12:00")

    # ------------------------------------------------------------------
    # datetime_format
    # ------------------------------------------------------------------

    def test_datetime_format_12h_datetime(self):
        """With 24h off, datetime_format includes date and 12h time."""
        result = datetime_format(self.aware_dt)
        local = timezone.localtime(self.aware_dt)
        time_str = formats.time_format(local, "TIME_FORMAT")
        date_str = formats.date_format(local, "DATE_FORMAT")
        self.assertEqual(result, "{} {}".format(date_str, time_str))

    def test_datetime_format_24h_datetime(self):
        """With 24h on, datetime_format includes date and HH:MM time."""
        self.settings.hour_format = True
        self.settings.save()

        result = datetime_format(self.aware_dt)
        local = timezone.localtime(self.aware_dt)
        time_str = local.strftime("%H:%M")
        date_str = formats.date_format(local, "DATE_FORMAT")
        self.assertEqual(result, "{} {}".format(date_str, time_str))
        self.assertNotIn("p.m.", result)
        self.assertNotIn("a.m.", result)

    def test_datetime_format_plain_date(self):
        """datetime_format on a plain date returns just the formatted date."""
        result = datetime_format(self.plain_date)
        expected = formats.date_format(self.plain_date, "DATE_FORMAT")
        self.assertEqual(result, expected)

    def test_datetime_format_none(self):
        self.assertEqual(datetime_format(None), "")

    # ------------------------------------------------------------------
    # datetime_short respects hour_format setting
    # ------------------------------------------------------------------

    def test_datetime_short_24h(self):
        """datetime_short uses HH:MM when 24h mode is enabled."""
        self.settings.hour_format = True
        self.settings.save()

        from core.templatetags.datetime import datetime_short

        date = timezone.localtime()
        result = datetime_short(date)
        local = timezone.localtime(date)
        self.assertIn(local.strftime("%H:%M"), result)
        self.assertNotIn("a.m.", result)
        self.assertNotIn("p.m.", result)

    def test_datetime_short_12h(self):
        """datetime_short uses locale TIME_FORMAT when 24h mode is off."""
        self.settings.hour_format = False
        self.settings.save()

        from core.templatetags.datetime import datetime_short

        date = timezone.localtime()
        result = datetime_short(date)
        expected_time = formats.date_format(date, "TIME_FORMAT")
        self.assertIn(expected_time, result)
