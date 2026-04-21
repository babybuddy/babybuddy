# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase
from django.utils import timezone

from core import models
from reports.graphs import medication_intervals


class MedicationIntervalsTestCase(TestCase):
    def setUp(self):
        self.original_tz = timezone.get_current_timezone()
        self.tz = dt.timezone(dt.timedelta(days=-1, hours=1))
        timezone.activate(self.tz)

    def tearDown(self):
        timezone.activate(self.original_tz)

    def test_medication_intervals(self):
        c = models.Child(birth_date=dt.datetime.now())
        c.save()

        models.Medication.objects.create(
            child=c,
            name="Tylenol",
            time=dt.datetime(2000, 1, 1, 0, 0, tzinfo=dt.timezone.utc),
        )
        models.Medication.objects.create(
            child=c,
            name="Tylenol",
            time=dt.datetime(2000, 1, 1, 4, 0, tzinfo=dt.timezone.utc),
        )

        medication_intervals(models.Medication.objects.order_by("time"))
