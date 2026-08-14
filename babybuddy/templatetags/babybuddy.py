# -*- coding: utf-8 -*-

from django import template
from django.apps import apps
from django.conf import settings
from django.templatetags.static import static
from django.utils import timezone
from django.utils.functional import lazy
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import to_locale, get_language, gettext_lazy as _

from axes.helpers import get_lockout_message
from axes.models import AccessAttempt

from core.models import Child

register = template.Library()
mark_safe_lazy = lazy(mark_safe, str)


@register.simple_tag
def axes_lockout_message():
    return get_lockout_message()


@register.simple_tag(takes_context=True)
def relative_url(context, field_name, value):
    """
    Create a relative URL with an updated field value.

    :param context: current request content.
    :param field_name: the field name to update.
    :param value: the new value for field_name.
    :return: encoded relative url with updated query string.
    """
    url = "?{}={}".format(field_name, value)
    querystring = context["request"].GET.urlencode().split("&")
    filtered_querystring = filter(lambda p: p.split("=")[0] != field_name, querystring)
    encoded_querystring = "&".join(filtered_querystring)
    return "{}&{}".format(url, encoded_querystring)


@register.simple_tag()
def version_string():
    """
    Get Baby Buddy's current version string.

    :return: version string ('n.n.n (commit)').
    """
    config = apps.get_app_config("babybuddy")
    return config.version_string


@register.simple_tag()
def get_current_locale():
    """
    Get the current language's locale code.

    :return: locale code (e.g. 'de', 'fr', etc.).
    """
    return to_locale(get_language())


# Django language codes -> Plotly locale file suffixes (plotly-locale-<code>.js).
# English uses Plotly's built-in locale and does not need an extra file.
PLOTLY_LOCALES = {
    "ca": "ca",
    "cs": "cs",
    "da": "da",
    "de": "de",
    "es": "es",
    "fi": "fi",
    "fr": "fr",
    "he": "he",
    "hr": "hr",
    "hu": "hu",
    "it": "it",
    "ja": "ja",
    "ko": "ko",
    "nb": "no",
    "nl": "nl",
    "pl": "pl",
    "pt": "pt-pt",
    "pt-br": "pt-br",
    "ru": "ru",
    "sr": "sr",
    "sv": "sv",
    "tr": "tr",
    "uk": "uk",
    "zh-hans": "zh-cn",
    "zh-hant": "zh-hk",
    "zh-tw": "zh-tw",
}


def plotly_locale_code(language=None):
    """
    Map a Django language code to a Plotly locale file suffix, or None.
    """
    lang = (language if language is not None else get_language() or "").lower()
    if not lang:
        return None
    if lang in PLOTLY_LOCALES:
        return PLOTLY_LOCALES[lang]
    return PLOTLY_LOCALES.get(lang.split("-")[0])


@register.simple_tag()
def plotly_locale_script():
    """
    Emit a deferred script tag for the current language's Plotly locale.
    """
    locale = plotly_locale_code()
    if not locale:
        return ""
    url = static(f"babybuddy/js/plotly-locale/plotly-locale-{locale}.js")
    return mark_safe(f'<script src="{url}" defer></script>')


@register.simple_tag()
def get_child_count():
    return Child.count()


@register.simple_tag()
def get_current_timezone():
    return timezone.get_current_timezone_name()


@register.simple_tag(takes_context=True)
def make_absolute_url(context, url):
    request = context["request"]
    abs_url = request.build_absolute_uri(url)
    return abs_url


@register.simple_tag()
def user_is_locked(user):
    return AccessAttempt.objects.filter(username=user.username).exists()


@register.simple_tag()
def user_is_read_only(user):
    return user.groups.filter(name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]).exists()


@register.simple_tag()
def confirm_delete_text(object):
    return mark_safe_lazy(
        _("Are you sure you want to delete %(name)s?")
        % {
            "name": format_html('<span class="text-info">{}</span>', str(object)),
        }
    )


@register.simple_tag()
def confirm_unlock_text(object):
    return mark_safe_lazy(
        _("Are you sure you want to unlock %(name)s?")
        % {
            "name": format_html('<span class="text-info">{}</span>', str(object)),
        }
    )
