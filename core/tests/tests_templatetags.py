# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone, formats

from core.models import Child, Timer
from core.templatetags import bootstrap, datetime, duration, timers


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

    def test_child_age_string(self):
        date = timezone.localdate() - timezone.timedelta(days=0, hours=6)
        self.assertEqual("0 days", duration.child_age_string(date))
        date = timezone.localdate() - timezone.timedelta(days=1, hours=6)
        self.assertEqual("1\xa0day", duration.child_age_string(date))
        date = timezone.localdate() - timezone.timedelta(days=45)
        self.assertEqual("1\xa0month", duration.child_age_string(date))
        date = timezone.localdate() - timezone.timedelta(days=95)
        self.assertEqual("3\xa0months", duration.child_age_string(date))

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

    def test_instance_add_url(self):
        child = Child.objects.create(
            first_name="Test", last_name="Child", birth_date=timezone.localdate()
        )
        user = User.objects.create_user(username="timer")
        timer = Timer.objects.create(user=user)

        url = timers.instance_add_url({"timer": timer}, "core:sleep-add")
        self.assertEqual(url, "/sleep/add/?timer={}".format(timer.id))

        timer = Timer.objects.create(user=user, child=child)
        url = timers.instance_add_url({"timer": timer}, "core:sleep-add")
        self.assertEqual(
            url, "/sleep/add/?timer={}&child={}".format(timer.id, child.slug)
        )

    def test_datetimepicker_format(self):
        request = MockUserRequest(User.objects.first())
        request.user.settings.dashboard_hide_empty = True
        context = {"request": request}

        with self.settings(USE_24_HOUR_TIME_FORMAT=False):
            self.assertEqual(datetime.datetimepicker_format(context), "L LT")
            self.assertEqual(datetime.datetimepicker_format(context, "L LT"), "L LT")
            self.assertEqual(datetime.datetimepicker_format(context, "L LTS"), "L LTS")

        with self.settings(USE_24_HOUR_TIME_FORMAT=True):
            self.assertEqual(datetime.datetimepicker_format(context), "L HH:mm")
            self.assertEqual(datetime.datetimepicker_format(context, "L LT"), "L HH:mm")
            self.assertEqual(
                datetime.datetimepicker_format(context, "L LTS"), "L HH:mm:ss"
            )

    @override_settings(USE_24_HOUR_TIME_FORMAT=False)
    def test_datetimepicker_format_en_gb(self):
        user = User.objects.first()
        user.settings.language = "en-GB"
        user.save()

        request = MockUserRequest(user)
        request.user.settings.dashboard_hide_empty = True
        context = {"request": request}

        self.assertEqual(datetime.datetimepicker_format(context), "L h:mm a")
        self.assertEqual(datetime.datetimepicker_format(context, "L LT"), "L h:mm a")
        self.assertEqual(
            datetime.datetimepicker_format(context, "L LTS"), "L h:mm:ss a"
        )

    def test_datetime_short(self):
        date = timezone.localtime()
        self.assertEqual(
            datetime.datetime_short(date),
            "Today, {}".format(formats.date_format(date, format="TIME_FORMAT")),
        )

        date = timezone.localtime() - timezone.timedelta(days=1, hours=6)
        self.assertEqual(
            datetime.datetime_short(date),
            "{}, {}".format(
                formats.date_format(date, format="SHORT_MONTH_DAY_FORMAT"),
                formats.date_format(date, format="TIME_FORMAT"),
            ),
        )

        date = timezone.localtime() - timezone.timedelta(days=500)
        self.assertEqual(
            datetime.datetime_short(date),
            formats.date_format(date, format="SHORT_DATETIME_FORMAT"),
        )
