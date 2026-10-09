# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase

from core import models

# The reference data covers roughly 23 to 40 weeks of gestation, i.e. every
# day from 119 days before term up to the day before term.
PRETERM_DAYS = 119


class PretermWeightPercentileTestCase(TestCase):
    """Tests for the preterm weight percentile data loaded by a migration."""

    def test_covers_every_day_before_term_for_both_sexes(self):
        for sex in ("boy", "girl"):
            ages = sorted(
                models.WeightPercentile.objects.filter(
                    sex=sex, age_in_days__lt=dt.timedelta(0)
                ).values_list("age_in_days", flat=True)
            )
            self.assertEqual(len(ages), PRETERM_DAYS, sex)
            self.assertEqual(len(set(ages)), PRETERM_DAYS, sex)
            self.assertEqual(ages[0], dt.timedelta(days=-PRETERM_DAYS), sex)
            self.assertEqual(ages[-1], dt.timedelta(days=-1), sex)

    def test_joins_the_term_data_without_a_gap(self):
        # The WHO data starts at term (age 0), so the combined reference curve
        # runs continuously across the due date.
        for sex in ("boy", "girl"):
            self.assertTrue(
                models.WeightPercentile.objects.filter(
                    sex=sex, age_in_days=dt.timedelta(0)
                ).exists(),
                sex,
            )

    def test_percentiles_increase_within_each_row(self):
        for row in models.WeightPercentile.objects.filter(
            age_in_days__lt=dt.timedelta(0)
        ):
            values = [
                row.p3_weight,
                row.p15_weight,
                row.p50_weight,
                row.p85_weight,
                row.p97_weight,
            ]
            self.assertEqual(
                values,
                sorted(values),
                "percentiles out of order for {} at {}".format(
                    row.sex, row.age_in_days
                ),
            )
            self.assertGreater(row.p3_weight, 0, row.sex)

    def test_medians_increase_with_gestational_age(self):
        for sex in ("boy", "girl"):
            medians = list(
                models.WeightPercentile.objects.filter(
                    sex=sex, age_in_days__lt=dt.timedelta(0)
                )
                .order_by("age_in_days")
                .values_list("p50_weight", flat=True)
            )
            self.assertEqual(medians, sorted(medians), sex)
