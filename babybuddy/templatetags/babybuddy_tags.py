# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.apps import apps

register = template.Library()


@register.simple_tag(takes_context=True)
def relative_url(context, field_name, value):
    """
    Create a relative URL with an updated field value.

    :param context: current request content.
    :param field_name: the field name to update.
    :param value: the new value for field_name.
    :return: encoded relative url with updated query string.
    """
    url = '?{}={}'.format(field_name, value)
    querystring = context['request'].GET.urlencode().split('&')
    filtered_querystring = filter(
        lambda p: p.split('=')[0] != field_name, querystring)
    encoded_querystring = '&'.join(filtered_querystring)
    return '{}&{}'.format(url, encoded_querystring)


@register.simple_tag()
def version_string():
    """
    Get Baby Buddy's current version string.

    :return: version string ('n.n.n (commit)')
    """
    config = apps.get_app_config('babybuddy')
    return config.version_string
