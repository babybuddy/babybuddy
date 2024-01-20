# -*- coding: utf-8 -*-
from django import template
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.translation import gettext as _

from datetime import date, datetime, time

from core import models

register = template.Library()

activities = {
    'sleep': {
        'icon': 'babybuddy/img/crib.svg',
        'color': 'purple',
        'title': 'Sleep',
        'model': models.Sleep
    },
    'changes': {
        'icon': 'babybuddy/img/diaper.svg',
        'color': 'yellow',
        'title': 'Diaper',
        'model': models.DiaperChange
    },
    'bottle': {
        'icon': 'babybuddy/img/feeding.svg',
        'color': 'green',
        'title': 'Feeding',
        'model': models.Feeding
    },
    'nursing': {
        'icon': 'babybuddy/img/nursing.svg',
        'color': 'green',
        'title': 'Nursing',
        'model': models.Feeding
    },
    'tummy': {
        'icon': 'babybuddy/img/tummy.svg',
        'color': 'purple',
        'title': 'Tummy Time',
        'model': models.TummyTime
    },
    'pumping': {
        'icon': 'babybuddy/img/feeding.svg',
        'color': 'green',
        'title': 'Pumping',
        'model': models.Pumping
    }

}

def get_last_instance(model, child, activity): 
    child_activities = model.objects.filter(child=child); 
    if activity == 'changes':
        return child_activities.order_by("-time").first()
    else:
        return child_activities.order_by("-end").first()

def since_last_instance(model, child, activity): 
    instance = get_last_instance(model, child, activity)
    if not instance:
        return
    if activity == 'changes':
        return instance.time;
    else:
        return instance.end;

@register.inclusion_tag("favorite.html", takes_context=True)
def favorite(context, activity_string, child):
    activity = activities[activity_string];
    since = since_last_instance(activity['model'], child, activity_string);
    print(since)
    result = activity.copy()
    result['since'] = since
    result['empty'] = not since
    return result
