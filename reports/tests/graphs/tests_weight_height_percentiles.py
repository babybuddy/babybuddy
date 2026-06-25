# -*- coding: utf-8 -*-
import datetime as dt

from django.test import TestCase

from core import models
from reports.graphs.weight_change import weight_change
from reports.graphs.height_change import height_change


class WeightHeightPercentilesTestCase(TestCase):
    def test_percentile_graphs(self):
        c = models.Child.objects.create(
            first_name="Test",
            last_name="Child",
            birth_date=dt.date(2025, 1, 1),
        )

        models.Weight.objects.create(
            child=c,
            weight=8.0,
            date=dt.date(2025, 10, 1),
        )

        models.Height.objects.create(
            child=c,
            height=70.0,
            date=dt.date(2025, 10, 1),
        )

        percentile_weights = models.WeightPercentile.objects.filter(sex="boy")
        percentile_heights = models.HeightPercentile.objects.filter(sex="boy")

        actual_weights = models.Weight.objects.filter(child=c)
        html_w, js_w = weight_change(actual_weights, percentile_weights, c.birth_date)
        self.assertIsNotNone(html_w)
        self.assertIsNotNone(js_w)

        actual_heights = models.Height.objects.filter(child=c)
        html_h, js_h = height_change(actual_heights, percentile_heights, c.birth_date)
        self.assertIsNotNone(html_h)
        self.assertIsNotNone(js_h)
