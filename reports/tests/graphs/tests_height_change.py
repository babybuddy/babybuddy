# -*- coding: utf-8 -*-
import datetime as dt
import re

from django.test import TestCase

from core import models
from reports.graphs.height_change import height_change

CORRECTED_AGE_NOTE = "Percentiles plotted by corrected age"


class HeightChangeCorrectedAgeTestCase(TestCase):
    """Tests for corrected-age handling in the height change graph."""

    def setUp(self):
        # Height percentile reference data is loaded by a data migration, so
        # reuse it rather than creating (conflicting) rows here.
        self.percentiles = models.HeightPercentile.objects.filter(sex="boy")
        self.assertTrue(self.percentiles.exists())

    def _child_with_heights(self, birth_date, due_date, measuring_dates):
        child = models.Child.objects.create(
            first_name="Pre",
            last_name="Term",
            birth_date=birth_date,
            due_date=due_date,
        )
        for i, date in enumerate(measuring_dates):
            models.Height.objects.create(child=child, date=date, height=50.0 + i)
        return child

    def _first_percentile_date(self, js, name="P3"):
        """The first date plotted for a percentile curve, i.e. its anchor."""
        trace = js[js.index('"name":"{}"'.format(name)) :]
        match = re.search(r'"x":\["(\d{4}-\d{2}-\d{2})"', trace)
        self.assertIsNotNone(match, "no percentile dates found for {}".format(name))
        return dt.date.fromisoformat(match.group(1))

    def test_corrected_age_note_shown_for_preterm(self):
        # Born 23 days before the due date -> percentiles use corrected age.
        birth_date = dt.date(2025, 6, 1)
        due_date = dt.date(2025, 6, 24)
        child = self._child_with_heights(
            birth_date,
            due_date,
            [dt.date(2025, 7, 1), dt.date(2025, 8, 1)],
        )
        html, js = height_change(
            models.Height.objects.filter(child=child),
            self.percentiles,
            child.birth_date,
            child.due_date,
        )
        self.assertIn(CORRECTED_AGE_NOTE, js)
        # The curves start at the due date rather than the birth date.
        self.assertEqual(self._first_percentile_date(js), due_date)

    def test_no_correction_without_due_date(self):
        birth_date = dt.date(2025, 6, 1)
        child = self._child_with_heights(
            birth_date,
            None,
            [dt.date(2025, 7, 1), dt.date(2025, 8, 1)],
        )
        html, js = height_change(
            models.Height.objects.filter(child=child),
            self.percentiles,
            child.birth_date,
            child.due_date,
        )
        self.assertNotIn(CORRECTED_AGE_NOTE, js)
        self.assertEqual(self._first_percentile_date(js), birth_date)

    def test_no_correction_when_due_date_before_birth(self):
        # Post-term birth: do not apply a (negative) correction.
        birth_date = dt.date(2025, 6, 24)
        due_date = dt.date(2025, 6, 1)
        child = self._child_with_heights(
            birth_date,
            due_date,
            [dt.date(2025, 7, 1)],
        )
        html, js = height_change(
            models.Height.objects.filter(child=child),
            self.percentiles,
            child.birth_date,
            child.due_date,
        )
        self.assertNotIn(CORRECTED_AGE_NOTE, js)
        self.assertEqual(self._first_percentile_date(js), birth_date)

    def test_no_note_without_percentile_data(self):
        # The plain height report has no percentile curves to correct, so its
        # title must not mention corrected age.
        birth_date = dt.date(2025, 6, 1)
        due_date = dt.date(2025, 6, 24)
        child = self._child_with_heights(
            birth_date,
            due_date,
            [dt.date(2025, 7, 1)],
        )
        html, js = height_change(
            models.Height.objects.filter(child=child),
            models.HeightPercentile.objects.filter(sex=None),
            child.birth_date,
            child.due_date,
        )
        self.assertNotIn(CORRECTED_AGE_NOTE, js)

    def test_preterm_with_only_early_measurements_does_not_raise(self):
        # Regression: when every measurement predates the due date, the last
        # one falls before the first (corrected) percentile point. This must
        # not raise (previously a list.index() lookup could fail).
        birth_date = dt.date(2025, 6, 1)
        due_date = dt.date(2025, 6, 24)
        child = self._child_with_heights(
            birth_date,
            due_date,
            [dt.date(2025, 6, 5), dt.date(2025, 6, 10)],
        )
        html, js = height_change(
            models.Height.objects.filter(child=child),
            self.percentiles,
            child.birth_date,
            child.due_date,
        )
        self.assertIsInstance(html, str)
        self.assertIsInstance(js, str)
