# -*- coding: utf-8 -*-
import datetime as dt
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone
import plotly.graph_objs as go

from core import models
from reports.graphs import sleep_pattern


class SleepPatternTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_sleep_pattern(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()

        models.Sleep.objects.create(
            child=c,
            start=dt.datetime(2000, 1, 1, 0, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2000, 1, 1, 0, 1, tzinfo=dt.timezone.utc),
        )

        sleep_pattern(models.Sleep.objects.order_by("start"))

    def _days(self, *sleeps):
        tz = ZoneInfo("America/New_York")
        timezone.activate(tz)
        c = models.Child.objects.create(birth_date=dt.date(2026, 1, 1))
        for start, end in sleeps:
            models.Sleep.objects.create(
                child=c,
                start=dt.datetime(*start, tzinfo=tz),
                end=dt.datetime(*end, tzinfo=tz),
            )
        with mock.patch.object(go, "Bar", wraps=go.Bar) as bar:
            sleep_pattern(models.Sleep.objects.order_by("start"))
        days = {}
        for i, x in enumerate(bar.call_args_list[0].kwargs["x"]):
            days[x[:10]] = [
                (call.kwargs["y"][i], call.kwargs["hovertext"][i])
                for call in bar.call_args_list
                if call.kwargs["y"][i] is not None
            ]
        return days

    def test_sleep_pattern_first_sleep_over_spring_forward(self):
        days = self._days(((2026, 3, 8, 1, 0), (2026, 3, 8, 5, 0)))
        self.assertEqual(
            days["2026-03-08"][-1],
            (240, "Asleep 3 hours, 0 minutes (1 a.m. to 5 a.m.)"),
        )

    def test_sleep_pattern_fall_back_leaves_day_before(self):
        days = self._days(
            ((2026, 10, 31, 13, 0), (2026, 10, 31, 15, 0)),
            ((2026, 11, 1, 1, 30), (2026, 11, 1, 5, 0)),
        )
        self.assertEqual(
            days["2026-10-31"][-1],
            (539, "Awake 8 hours, 59 minutes (3 p.m. to 11:59 p.m.)"),
        )
        self.assertEqual(
            days["2026-11-01"][-1],
            (210, "Asleep 4 hours, 30 minutes (1:30 a.m. to 5 a.m.)"),
        )
