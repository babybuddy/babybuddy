# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template

from core.models import Feeding


register = template.Library()


@register.inclusion_tag('cards/feeding_last.html')
def card_feeding_last(child):
    feeding_instance = Feeding.objects.filter(child=child).last()
    return {'feeding': feeding_instance}
