# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from core.models import DiaperChange, Feeding


register = template.Library()


@register.inclusion_tag('cards/feeding_last.html')
def card_feeding_last(child):
    feeding_instance = Feeding.objects.filter(
        child=child).order_by('-end').first()
    return {'feeding': feeding_instance}


@register.inclusion_tag('cards/diaperchange_last.html')
def card_diaperchange_last(child):
    feeding_instance = DiaperChange.objects.filter(
        child=child).order_by('-time').first()
    return {'change': feeding_instance}
