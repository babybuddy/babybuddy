# -*- coding: utf-8 -*-
from django import template

from babybuddy.plugins import get_installed_plugins

register = template.Library()


@register.inclusion_tag("dashboard/plugin_cards.html", takes_context=True)
def plugin_cards(context, child):
    """
    Render dashboard cards contributed by installed plugins.

    Each plugin that sets ``babybuddy_has_dashboard_card = True`` must
    provide a template at ``templates/<app_label>/cards/summary.html``
    that accepts a ``child`` context variable.
    """
    cards = [
        {
            "config": plugin,
            "template": f"{plugin.label}/cards/summary.html",
        }
        for plugin in get_installed_plugins()
        if plugin.babybuddy_has_dashboard_card
    ]
    return {
        "plugin_cards": cards,
        "child": child,
        "request": context["request"],
    }
