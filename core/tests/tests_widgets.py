# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from core.widgets import DatalistTextInput


class DatalistTextInputTestCase(SimpleTestCase):
    def test_extra_attrs_without_suggestions(self):
        widget = DatalistTextInput(
            attrs={"maxlength": "10", "autocomplete": "on"}, datalist_id="test-list"
        )
        html = widget.render("name", "")
        self.assertIn('maxlength="10"', html)
        self.assertIn('list="test-list"', html)
        # Passed attrs override the widget's defaults.
        self.assertIn('autocomplete="on"', html)
        self.assertNotIn("<datalist", html)

    def test_suggestions_are_limited(self):
        widget = DatalistTextInput(
            suggestions=lambda: ["One", "Two", "Three"],
            datalist_id="test-list",
            limit=2,
        )
        html = widget.render("name", "")
        self.assertIn('<datalist id="test-list">', html)
        self.assertIn('<option value="One">', html)
        self.assertIn('<option value="Two">', html)
        self.assertNotIn('<option value="Three">', html)
