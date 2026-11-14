# -*- coding: utf-8 -*-
import datetime as dt
from unittest import mock
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.utils import timezone
import plotly.graph_objs as go

from core import models
from reports.graphs import feeding_pattern


class FeedingPatternTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_feeding_pattern(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()

        models.Feeding.objects.create(
            child=c,
            start=dt.datetime(2000, 1, 1, 0, 0, tzinfo=dt.timezone.utc),
            end=dt.datetime(2000, 1, 1, 0, 1, tzinfo=dt.timezone.utc),
        )

        feeding_pattern(models.Feeding.objects.order_by("start"))

    def _days(self, *feedings):
        tz = ZoneInfo("America/New_York")
        timezone.activate(tz)
        c = models.Child.objects.create(birth_date=dt.date(2026, 1, 1))
        for start, end in feedings:
            models.Feeding.objects.create(
                child=c,
                start=dt.datetime(*start, tzinfo=tz),
                end=dt.datetime(*end, tzinfo=tz),
                type="breast milk",
                method="left breast",
            )
        with mock.patch.object(go, "Bar", wraps=go.Bar) as bar:
            feeding_pattern(models.Feeding.objects.order_by("start"))
        days = {}
        for i, x in enumerate(bar.call_args_list[0].kwargs["x"]):
            days[x[:10]] = [
                (call.kwargs["y"][i], call.kwargs["hovertext"][i])
                for call in bar.call_args_list
                if call.kwargs["y"][i] is not None
            ]
        return days

    def test_feeding_pattern_first_feeding_over_spring_forward(self):
        days = self._days(((2026, 3, 8, 1, 45), (2026, 3, 8, 3, 15)))
        self.assertEqual(
            days["2026-03-08"][-1],
            (90, "Left breast feeding 30 minutes (1:45 a.m. to 3:15 a.m.)"),
        )

    def test_feeding_pattern_fall_back_leaves_day_before(self):
        days = self._days(
            ((2026, 10, 31, 13, 0), (2026, 10, 31, 13, 30)),
            ((2026, 11, 1, 1, 30), (2026, 11, 1, 2, 0)),
        )
        self.assertEqual(days["2026-10-31"][-1], (629, None))
        self.assertEqual(
            days["2026-11-01"][-1],
            (30, "Left breast feeding 1 hour, 30 minutes (1:30 a.m. to 2 a.m.)"),
        )
