# -*- coding: utf-8 -*-
from django.test import SimpleTestCase

from reports.utils import split_graph_output


class SplitGraphOutputTestCase(SimpleTestCase):
    def test_wraps_plotly_script_for_deferred_graph_js(self):
        output = (
            '<div id="chart"></div>'
            '<script type="text/javascript">Plotly.newPlot("chart", []);</script>'
        )
        html, js = split_graph_output(output)
        self.assertEqual(html, '<div id="chart"></div>')
        self.assertIn("BabyBuddyReady", js)
        self.assertIn('Plotly.newPlot("chart", []);', js)
        self.assertTrue(js.startswith("<script"))
        self.assertTrue(js.endswith("</script>"))
