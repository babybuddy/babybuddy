# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from core.models import DiaperChange, Feeding, Sleep, TummyTime


register = template.Library()


@register.inclusion_tag('cards/feeding_last.html')
def card_feeding_last(child):
    instance = Feeding.objects.filter(child=child).order_by('-end').first()
    return {'feeding': instance}


@register.inclusion_tag('cards/diaperchange_last.html')
def card_diaperchange_last(child):
    instance = DiaperChange.objects.filter(
        child=child).order_by('-time').first()
    return {'change': instance}


@register.inclusion_tag('cards/tummytime_last.html')
def card_tummytime_last(child):
    instance = TummyTime.objects.filter(child=child).order_by('-end').first()
    return {'tummytime': instance}


@register.inclusion_tag('cards/sleep_last.html')
def card_sleep_last(child):
    instance = Sleep.objects.filter(child=child).order_by('-end').first()
    return {'sleep': instance}
