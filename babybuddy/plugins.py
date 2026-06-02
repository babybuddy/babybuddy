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
    # Set both to add a top-level nav item.
    babybuddy_nav_label = None  # e.g. "Books"
    babybuddy_nav_url_name = None  # e.g. "books:book-list"
    babybuddy_nav_icon = "icon-note"  # CSS class from babybuddy icon font

    # --- Dashboard ---
    # Set True and provide templates/<app_label>/cards/summary.html
    babybuddy_has_dashboard_card = False

    # --- API ---
    # Set True and provide api.py with register_api(router) function
    babybuddy_has_api = False

    # --- Quick Entry ---
    # Dotted path to a handler class. Wired up when quick-entry is in main.
    babybuddy_quick_entry_handler = None


def get_installed_plugins():
    """Return all installed ``BabyBuddyPluginConfig`` instances."""
    from django.apps import apps

    return [
        cfg
        for cfg in apps.get_app_configs()
        if isinstance(cfg, BabyBuddyPluginConfig)
    ]


def plugin_context(request):
    """
    Context processor that injects plugin nav items into every template.

    Add to ``TEMPLATES[0]["OPTIONS"]["context_processors"]`` in settings.
    """
    nav_items = []
    for plugin in get_installed_plugins():
        if plugin.babybuddy_nav_label and plugin.babybuddy_nav_url_name:
            nav_items.append(
                {
                    "label": plugin.babybuddy_nav_label,
                    "url_name": plugin.babybuddy_nav_url_name,
                    "icon": plugin.babybuddy_nav_icon,
                }
            )
    return {"babybuddy_plugin_nav_items": nav_items}
