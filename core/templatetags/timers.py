# -*- coding: utf-8 -*-
from django import template
from django.urls import reverse

from core.models import Timer, Child

register = template.Library()


@register.inclusion_tag("core/timer_nav.html", takes_context=True)
def timer_nav(context):
    """
    Get a list of Timer instances to include in the nav menu.
    :param context: Django's context data.
    :returns: a dictionary with timers data.
    """
    request = context["request"] or None
    timers = Timer.objects.filter()
    children = Child.objects.all()
    perms = context["perms"] or None
    # The 'next' parameter is currently not used.
    return {
        "timers": timers,
        "children": children,
        "perms": perms,
        "next": request.path,
    }


@register.inclusion_tag("core/quick_timer_nav.html", takes_context=True)
def quick_timer_nav(context):
    children = Child.objects.all()
    perms = context["perms"] or None
    return {"children": children, "perms": perms}


@register.simple_tag(takes_context=True)
def instance_add_url(context, url_name):
    timer = context["timer"]
    url = "{}?timer={}".format(reverse(url_name), timer.id)
    if timer.child:
        url += "&child={}".format(timer.child.slug)
    return url
