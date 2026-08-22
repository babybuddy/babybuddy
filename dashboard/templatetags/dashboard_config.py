from django import template
from django.template.loader import render_to_string
import json

register = template.Library()


@register.simple_tag(takes_context=True)
def card_visible(context, card_name):
    """Check if a dashboard card should be visible based on user config."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return True
    config = request.user.settings.dashboard_card_config or {}
    card_config = config.get(card_name, {})
    return card_config.get("visible", True)


@register.simple_tag(takes_context=True)
def card_order_json(context):
    """Return saved card order as a JSON array string for JS reordering."""
    request = context.get("request")
    if not request or not request.user.is_authenticated:
        return "[]"
    config = request.user.settings.dashboard_card_config or {}
    order = config.get("_card_order", [])
    return json.dumps(order)
