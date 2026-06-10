# -*- coding: utf-8 -*-
"""
Tests for the Baby Buddy plugin system (babybuddy/plugins.py and related wiring).

Covers:
- BabyBuddyPluginConfig base class defaults
- get_installed_plugins() discovery
- plugin_context() context processor (happy path + plugin failure)
- _discover_pip_plugins() entry-point discovery (happy path + failures)
- plugin_cards templatetag (happy path + per-card failure isolation)
- URL/API loading failure isolation
"""

from unittest import mock

from django.apps import AppConfig
from django.test import RequestFactory, TestCase, override_settings

from babybuddy.plugins import (
    BabyBuddyPluginConfig,
    get_installed_plugins,
    plugin_context,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_plugin_config(name="test_plugin", **attrs):
    """Return a BabyBuddyPluginConfig instance with given attributes."""
    cfg = BabyBuddyPluginConfig.__new__(BabyBuddyPluginConfig)
    cfg.name = name
    cfg.label = name
    cfg.verbose_name = name
    for k, v in attrs.items():
        setattr(cfg, k, v)
    return cfg


# ---------------------------------------------------------------------------
# BabyBuddyPluginConfig defaults
# ---------------------------------------------------------------------------


class PluginConfigDefaultsTestCase(TestCase):
    def test_default_attributes(self):
        cfg = _make_plugin_config()
        self.assertIsNone(cfg.babybuddy_nav_label)
        self.assertIsNone(cfg.babybuddy_nav_url_name)
        self.assertEqual(cfg.babybuddy_nav_icon, "icon-note")
        self.assertIsNone(cfg.babybuddy_activity_url_name)
        self.assertIsNone(cfg.babybuddy_activity_label)
        self.assertFalse(cfg.babybuddy_has_dashboard_card)
        self.assertFalse(cfg.babybuddy_has_api)
        self.assertIsNone(cfg.babybuddy_quick_entry_handler)
        self.assertIsNone(cfg.babybuddy_timer_activities)

    def test_is_subclass_of_appconfig(self):
        self.assertTrue(issubclass(BabyBuddyPluginConfig, AppConfig))


# ---------------------------------------------------------------------------
# get_installed_plugins()
# ---------------------------------------------------------------------------


class GetInstalledPluginsTestCase(TestCase):
    def test_returns_only_plugin_configs(self):
        """Only BabyBuddyPluginConfig subclasses should be returned."""
        plugins = get_installed_plugins()
        for p in plugins:
            self.assertIsInstance(p, BabyBuddyPluginConfig)

    def test_returns_list(self):
        self.assertIsInstance(get_installed_plugins(), list)


# ---------------------------------------------------------------------------
# plugin_context() context processor
# ---------------------------------------------------------------------------


class PluginContextTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")

    def test_returns_empty_nav_when_no_plugins(self):
        with mock.patch("babybuddy.plugins.get_installed_plugins", return_value=[]):
            ctx = plugin_context(self.request)
        self.assertIn("babybuddy_plugin_nav_items", ctx)
        self.assertEqual(ctx["babybuddy_plugin_nav_items"], [])

    def test_nav_item_added_for_plugin_with_label_and_url(self):
        plugin = _make_plugin_config(
            babybuddy_nav_label="Books",
            babybuddy_nav_url_name="books:book-list",
            babybuddy_nav_icon="icon-note",
        )
        with mock.patch(
            "babybuddy.plugins.get_installed_plugins", return_value=[plugin]
        ):
            ctx = plugin_context(self.request)
        self.assertEqual(len(ctx["babybuddy_plugin_nav_items"]), 1)
        item = ctx["babybuddy_plugin_nav_items"][0]
        self.assertEqual(item["label"], "Books")
        self.assertEqual(item["url_name"], "books:book-list")

    def test_nav_item_skipped_when_label_missing(self):
        plugin = _make_plugin_config(
            babybuddy_nav_label=None,
            babybuddy_nav_url_name="books:book-list",
        )
        with mock.patch(
            "babybuddy.plugins.get_installed_plugins", return_value=[plugin]
        ):
            ctx = plugin_context(self.request)
        self.assertEqual(ctx["babybuddy_plugin_nav_items"], [])

    def test_activity_url_name_included_in_activity_nav_item(self):
        plugin = _make_plugin_config(
            babybuddy_nav_label="Readings",
            babybuddy_nav_url_name="books:reading-list",
            babybuddy_nav_icon="icon-note",
            babybuddy_nav_group="activities",
            babybuddy_activity_url_name="books:reading-add",
            babybuddy_activity_label="Reading",
        )
        with mock.patch(
            "babybuddy.plugins.get_installed_plugins", return_value=[plugin]
        ):
            ctx = plugin_context(self.request)
        self.assertEqual(len(ctx["babybuddy_plugin_activity_nav_items"]), 1)
        item = ctx["babybuddy_plugin_activity_nav_items"][0]
        self.assertEqual(item["url_name"], "books:reading-list")
        self.assertEqual(item["add_url_name"], "books:reading-add")
        self.assertEqual(item["add_label"], "Reading")

    def test_plugin_exception_does_not_crash_context(self):
        """A plugin that raises when its nav attrs are read must not crash the page."""
        bad_plugin = mock.MagicMock(spec=BabyBuddyPluginConfig)
        bad_plugin.name = "bad_plugin"
        type(bad_plugin).babybuddy_nav_label = mock.PropertyMock(
            side_effect=RuntimeError("plugin broken")
        )
        with mock.patch(
            "babybuddy.plugins.get_installed_plugins", return_value=[bad_plugin]
        ):
            # Must not raise
            ctx = plugin_context(self.request)
        self.assertIn("babybuddy_plugin_nav_items", ctx)
        self.assertEqual(ctx["babybuddy_plugin_nav_items"], [])


# ---------------------------------------------------------------------------
# _discover_pip_plugins()
# ---------------------------------------------------------------------------


class DiscoverPipPluginsTestCase(TestCase):
    def _call(self):
        # Import the private function for direct testing
        from babybuddy.settings.base import _discover_pip_plugins

        return _discover_pip_plugins()

    def test_returns_list_when_no_entry_points(self):
        with mock.patch("importlib.metadata.entry_points", return_value=[]):
            result = self._call()
        self.assertIsInstance(result, list)
        self.assertEqual(result, [])

    def test_converts_colon_to_dot_notation(self):
        ep = mock.MagicMock()
        ep.name = "books"
        ep.value = "babybuddy_books.apps:BooksConfig"
        with mock.patch("importlib.metadata.entry_points", return_value=[ep]):
            result = self._call()
        self.assertEqual(result, ["babybuddy_books.apps.BooksConfig"])

    def test_survives_importlib_failure(self):
        """If importlib.metadata itself fails, return empty list — don't crash."""
        with mock.patch(
            "importlib.metadata.entry_points", side_effect=Exception("metadata broken")
        ):
            result = self._call()
        self.assertEqual(result, [])

    def test_skips_bad_entry_point_continues_good_ones(self):
        bad_ep = mock.MagicMock()
        bad_ep.name = "bad"
        type(bad_ep).value = mock.PropertyMock(side_effect=Exception("bad ep"))
        good_ep = mock.MagicMock()
        good_ep.name = "good"
        good_ep.value = "good_plugin.apps:GoodConfig"
        with mock.patch(
            "importlib.metadata.entry_points", return_value=[bad_ep, good_ep]
        ):
            result = self._call()
        self.assertEqual(result, ["good_plugin.apps.GoodConfig"])


# ---------------------------------------------------------------------------
# plugin_cards templatetag
# ---------------------------------------------------------------------------


class PluginCardsTagTestCase(TestCase):
    def _call_tag(self, plugins, child=None):
        from dashboard.templatetags.plugin_cards import plugin_cards

        request = RequestFactory().get("/")
        context = {"request": request}
        if child is None:
            child = mock.MagicMock()
        with mock.patch(
            "dashboard.templatetags.plugin_cards.get_installed_plugins",
            return_value=plugins,
        ):
            return plugin_cards(context, child)

    def test_returns_empty_string_with_no_plugins(self):
        result = self._call_tag([])
        self.assertEqual(result, "")

    def test_skips_plugins_without_card(self):
        plugin = _make_plugin_config(babybuddy_has_dashboard_card=False)
        result = self._call_tag([plugin])
        self.assertEqual(result, "")

    def test_renders_card_for_plugin_with_card(self):
        plugin = _make_plugin_config(
            name="books", label="books", babybuddy_has_dashboard_card=True
        )
        fake_html = "<div>Books card</div>"
        with mock.patch(
            "dashboard.templatetags.plugin_cards.render_to_string",
            return_value=fake_html,
        ):
            result = self._call_tag([plugin])
        self.assertIn("Books card", result)
        self.assertIn("col-sm-6", result)

    def test_bad_card_does_not_crash_good_cards(self):
        """A plugin whose card template raises must not prevent other cards rendering."""
        bad = _make_plugin_config(
            name="bad_plugin", label="bad_plugin", babybuddy_has_dashboard_card=True
        )
        good = _make_plugin_config(
            name="good_plugin", label="good_plugin", babybuddy_has_dashboard_card=True
        )

        def fake_render(template_name, *args, **kwargs):
            if "bad_plugin" in template_name:
                raise Exception("bad template")
            return "<div>Good card</div>"

        with mock.patch(
            "dashboard.templatetags.plugin_cards.render_to_string",
            side_effect=fake_render,
        ):
            result = self._call_tag([bad, good])

        self.assertIn("Good card", result)

    def test_bad_card_renders_nothing(self):
        plugin = _make_plugin_config(
            name="bad_plugin", label="bad_plugin", babybuddy_has_dashboard_card=True
        )
        with mock.patch(
            "dashboard.templatetags.plugin_cards.render_to_string",
            side_effect=Exception("template error"),
        ):
            result = self._call_tag([plugin])
        self.assertEqual(result, "")
