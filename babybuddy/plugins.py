# -*- coding: utf-8 -*-
"""
Baby Buddy Plugin System
========================

Plugins are standard Django apps whose AppConfig subclasses
``BabyBuddyPluginConfig`` instead of ``AppConfig``. Baby Buddy
auto-discovers installed plugins and wires them into the dashboard,
nav, API, and (eventually) Quick Entry.

Installation (two paths)
------------------------
**During development** — add the app to ``INSTALLED_APPS`` in settings:

    INSTALLED_APPS = [..., "babybuddy_books.apps.BooksConfig"]

**Via pip** — declare an entry point in ``pyproject.toml``:

    [project.entry-points."babybuddy.plugins"]
    books = "babybuddy_books.apps:BooksConfig"

    Then ``pip install`` the package; Baby Buddy discovers it automatically.

Authoring a plugin
------------------
Minimal example::

    # myapp/apps.py
    from babybuddy.plugins import BabyBuddyPluginConfig

    class MyAppConfig(BabyBuddyPluginConfig):
        name = "myapp"
        verbose_name = "My App"

        babybuddy_nav_label = "My App"
        babybuddy_nav_url_name = "myapp:index"
        babybuddy_nav_icon = "icon-note"
        babybuddy_has_dashboard_card = True
        babybuddy_has_api = True

Extension points
----------------
- **Nav**: set ``babybuddy_nav_label`` + ``babybuddy_nav_url_name``.
- **Dashboard card**: set ``babybuddy_has_dashboard_card = True`` and
  provide ``templates/<app_label>/cards/summary.html``.
- **API**: set ``babybuddy_has_api = True`` and provide an ``api.py``
  module with a ``register_api(router)`` function.
- **Quick Entry**: set ``babybuddy_quick_entry_handler`` to the dotted
  path of a handler class (integration wired when quick-entry merges
  to main).
"""

from django.apps import AppConfig


class BabyBuddyPluginConfig(AppConfig):
    """
    Base AppConfig for Baby Buddy plugins.

    Subclass this instead of ``AppConfig`` to integrate with Baby Buddy.
    """

    # --- Nav ---
    # Set both to add a nav item.
    babybuddy_nav_label = None  # e.g. "Books"
    babybuddy_nav_url_name = None  # e.g. "books:book-list"
    babybuddy_nav_icon = "icon-note"  # CSS class from babybuddy icon font
    # Set to "activities" to nest under the Activities dropdown instead of top-level.
    babybuddy_nav_group = None
    # If set, renders an indented "+ add" link in the Activities dropdown (like core activities).
    # babybuddy_nav_url_name is used for the list link; this for the add link.
    babybuddy_activity_url_name = None
    # Label for the add link (e.g. "Reading" when nav_label is "Readings").
    # Defaults to babybuddy_nav_label if not set.
    babybuddy_activity_label = None

    # --- Dashboard ---
    # Set True and provide templates/<app_label>/cards/summary.html
    babybuddy_has_dashboard_card = False

    # --- API ---
    # Set True and provide api.py with register_api(router) function
    babybuddy_has_api = False

    # --- Quick Entry ---
    # Dotted path to a handler class. Wired up when quick-entry is in main.
    babybuddy_quick_entry_handler = None

    # --- Timer activities ---
    # List of dicts shown as buttons on the timer detail page.
    # Each dict: {"permission": "app.add_model", "url_name": "app:add", "label": "...", "icon": "icon-..."}
    # "permission" is required; activities without it are skipped.
    babybuddy_timer_activities = None


def get_installed_plugins():
    """Return all installed ``BabyBuddyPluginConfig`` instances."""
    from django.apps import apps

    return [
        cfg for cfg in apps.get_app_configs() if isinstance(cfg, BabyBuddyPluginConfig)
    ]


def plugin_context(request):
    """
    Context processor that injects plugin nav items into every template.

    Failures for individual plugins are logged and skipped so a broken
    plugin never prevents page rendering.
    """
    import logging

    logger = logging.getLogger("babybuddy.plugins")
    nav_items = []
    activity_nav_items = []
    timer_activities = []
    for plugin in get_installed_plugins():
        try:
            if plugin.babybuddy_nav_label and plugin.babybuddy_nav_url_name:
                item = {
                    "label": plugin.babybuddy_nav_label,
                    "url_name": plugin.babybuddy_nav_url_name,
                    "icon": plugin.babybuddy_nav_icon,
                    "add_url_name": plugin.babybuddy_activity_url_name,
                    "add_label": plugin.babybuddy_activity_label
                    or plugin.babybuddy_nav_label,
                }
                if plugin.babybuddy_nav_group == "activities":
                    activity_nav_items.append(item)
                else:
                    nav_items.append(item)
        except Exception as exc:
            logger.error("Plugin %r: failed to build nav item: %s", plugin.name, exc)
        try:
            for activity in plugin.babybuddy_timer_activities or []:
                perm = activity.get("permission")
                if not perm:
                    logger.warning(
                        "Plugin %r: timer activity %r has no 'permission' key — skipped",
                        plugin.name,
                        activity.get("label"),
                    )
                    continue
                if not activity.get("url_name") or not activity.get("label"):
                    logger.warning(
                        "Plugin %r: timer activity missing required 'url_name' or 'label' key — skipped",
                        plugin.name,
                    )
                    continue
                if request.user.has_perm(perm):
                    timer_activities.append(activity)
        except Exception as exc:
            logger.error(
                "Plugin %r: failed to build timer activities: %s", plugin.name, exc
            )
    return {
        "babybuddy_plugin_nav_items": nav_items,
        "babybuddy_plugin_activity_nav_items": activity_nav_items,
        "babybuddy_plugin_timer_activities": timer_activities,
    }
