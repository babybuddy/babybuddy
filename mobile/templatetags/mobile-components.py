# -*- coding: utf-8 -*-
from django import template
from django.utils.translation import gettext as _

from mobile.constants import activities

register = template.Library()


def get_last_instance(model, child, activity):
    child_activities = model.objects.filter(child=child)
    if activity == "changes":
        return child_activities.order_by("-time").first()
    else:
        return child_activities.order_by("-end").first()


def since_last_instance(model, child, activity):
    instance = get_last_instance(model, child, activity)
    if not instance:
        return
    if activity == "changes":
        return instance.time
    else:
        return instance.end


@register.inclusion_tag("favorite.html", takes_context=True)
def favorite(context, activity_string, child):
    activity = activities[activity_string]
    since = since_last_instance(activity["model"], child, activity_string)
    result = activity.copy()
    result["since"] = since
    result["empty"] = not since
    return result
