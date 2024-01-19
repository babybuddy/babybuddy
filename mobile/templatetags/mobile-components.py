# -*- coding: utf-8 -*-
from django import template
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext as _

from datetime import date, datetime, time

from core import models

register = template.Library()

def _filter_data_age(context, keyword="end"):
    filter = {}
    if context["request"].user.settings.dashboard_hide_age:
        now = timezone.localtime()
        start_time = now - context["request"].user.settings.dashboard_hide_age
        filter[keyword + "__range"] = (start_time, now)
    return filter


@register.inclusion_tag("favorite.html", takes_context=True)
def favorite(context, child):
    """
    Information about the most recent feeding.
    :param child: an instance of the Child model.
    :returns: a dictionary with the most recent Feeding instance.
    """
    instance = (
        models.Feeding.objects.filter(child=child)
        .filter(**_filter_data_age(context))
        .order_by("-end")
        .first()
    )
    empty = not instance

    return {
        "type": "feeding",
        "feeding": instance,
        "empty": empty,
        "hide_empty": _hide_empty(context),
    }

def test_tag(context, child):
  return "BOOP"