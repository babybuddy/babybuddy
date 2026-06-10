# -*- coding: utf-8 -*-
import logging

from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from babybuddy.plugins import get_installed_plugins

register = template.Library()
logger = logging.getLogger("babybuddy.plugins")


@register.simple_tag(takes_context=True)
def plugin_cards(context, child):
    """
    Render dashboard cards from all installed plugins that declare
    ``babybuddy_has_dashboard_card = True``.

    Each card is rendered independently. If one plugin's card template
    raises any exception it is logged and skipped — other cards and the
    rest of the dashboard are unaffected.

    Each plugin must provide: ``templates/<app_label>/cards/summary.html``
    """
    request = context.get("request")
    rendered = []

    for plugin in get_installed_plugins():
        try:
            if not plugin.babybuddy_has_dashboard_card:
                continue

            template_name = f"{plugin.label}/cards/summary.html"
            hide_empty = False
            if (
                request
                and hasattr(request, "user")
                and hasattr(request.user, "settings")
            ):
                hide_empty = request.user.settings.dashboard_hide_empty
            html = render_to_string(
                template_name,
                {"child": child, "request": request, "hide_empty": hide_empty},
                request=request,
            )
            rendered.append(f'<div class="col-sm-6 col-lg-4">{html}</div>')
        except Exception as exc:
            logger.error(
                "Plugin %r: dashboard card %r failed to render: %s",
                plugin.name,
                template_name,
                exc,
            )

    return mark_safe("".join(rendered))
