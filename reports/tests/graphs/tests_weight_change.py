# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase

from core import models
from reports.graphs.weight_change import weight_change

CORRECTED_AGE_NOTE = "Percentiles plotted by corrected age"


class WeightChangeCorrectedAgeTestCase(TestCase):
    """Tests for corrected-age handling in the weight change graph."""

    def setUp(self):
        # Weight percentile reference data is loaded by a data migration, so
        # reuse it rather than creating (conflicting) rows here.
        self.percentiles = models.WeightPercentile.objects.filter(sex="boy")
        self.assertTrue(self.percentiles.exists())

    def _child_with_weights(self, birth_date, due_date, weigh_dates):
        child = models.Child.objects.create(
            first_name="Pre",
            last_name="Term",
            birth_date=birth_date,
            due_date=due_date,
        )
        for i, date in enumerate(weigh_dates):
            models.Weight.objects.create(child=child, date=date, weight=3.0 + i)
        return child

    def test_corrected_age_note_shown_for_preterm(self):
        # Born 23 days before the due date -> percentiles use corrected age.
        birth_date = dt.date(2025, 6, 1)
        due_date = dt.date(2025, 6, 24)
        child = self._child_with_weights(
            birth_date,
            due_date,
            [dt.date(2025, 7, 1), dt.date(2025, 8, 1)],
        )
        html, js = weight_change(
            models.Weight.objects.filter(child=child),
            self.percentiles,
            child.birth_date,
            child.due_date,
        )
        self.assertIn(CORRECTED_AGE_NOTE, js)

    def test_no_correction_without_due_date(self):
        birth_date = dt.date(2025, 6, 1)
        child = self._child_with_weights(
            birth_date,
            None,
            [dt.date(2025, 7, 1), dt.date(2025, 8, 1)],
        )
        html, js = weight_change(
            models.Weight.objects.filter(child=child),
            self.percentiles,
            child.birth_date,
            child.due_date,
        )
        self.assertNotIn(CORRECTED_AGE_NOTE, js)

    def test_no_correction_when_due_date_before_birth(self):
        # Post-term birth: do not apply a (negative) correction.
        birth_date = dt.date(2025, 6, 24)
        due_date = dt.date(2025, 6, 1)
        child = self._child_with_weights(
            birth_date,
            due_date,
            [dt.date(2025, 7, 1)],
        )
        html, js = weight_change(
            models.Weight.objects.filter(child=child),
            self.percentiles,
            child.birth_date,
            child.due_date,
        )
        self.assertNotIn(CORRECTED_AGE_NOTE, js)

    def test_preterm_with_only_early_measurements_does_not_raise(self):
        # Regression: when every weigh-in predates the due date, the last
        # measurement falls before the first (corrected) percentile point.
        # This must not raise (previously a list.index() lookup could fail).
        birth_date = dt.date(2025, 6, 1)
        due_date = dt.date(2025, 6, 24)
        child = self._child_with_weights(
            birth_date,
            due_date,
            [dt.date(2025, 6, 5), dt.date(2025, 6, 10)],
        )
        html, js = weight_change(
            models.Weight.objects.filter(child=child),
            self.percentiles,
            child.birth_date,
            child.due_date,
        )
        self.assertIsInstance(html, str)
        self.assertIsInstance(js, str)
