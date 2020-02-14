# -*- coding: utf-8 -*-
from django import template
from django.apps import apps
from django.utils import timezone
from django.utils.translation import to_locale, get_language

from core.models import Child

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

    :return: version string ('n.n.n (commit)').
    """
    config = apps.get_app_config('babybuddy')
    return config.version_string


@register.simple_tag()
def get_current_locale():
    """
    Get the current language's locale code.

    :return: locale code (e.g. 'de', 'fr', etc.).
    """
    return to_locale(get_language())


@register.simple_tag()
def get_child_count():
    return Child.count()


@register.simple_tag()
def get_current_timezone():
    return timezone.get_current_timezone_name()
