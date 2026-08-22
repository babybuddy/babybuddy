# -*- coding: utf-8 -*-

import datetime
import os

from django import template
from django.apps import apps
from django.conf import settings
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
def dev_build_banner():
    """
    Dev deployment build banner (fork-only; feat/dev-tools lane).

    Reads BB_BUILD_TAG / BB_BUILD_TIME baked into the image as ENV by CI
    (see test-docker/Dockerfile and .gitea/workflows/ci.yml). Returns an
    empty string when unset — bare test runs and upstream source trees —
    so the user menu renders identically to stock Baby Buddy.

    BB_BUILD_TIME is baked as a UTC string ("2026-08-20 22:28 UTC").
    Localize it to the user's timezone at render (UserTimezoneMiddleware
    has already activated it for the request) — never display UTC to the
    user. Unparseable values pass through untouched.
    """
    tag = os.environ.get("BB_BUILD_TAG", "").strip()
    built = os.environ.get("BB_BUILD_TIME", "").strip()
    if not tag:
        return ""
    if built:
        return "{} · {}".format(tag, _localize_build_time(built))
    return tag


def _localize_build_time(raw: str) -> str:
    """UTC build-time env -> user's wall clock, format 'YYYY-MM-DD HH:MM'."""
    try:
        naive = datetime.datetime.strptime(
            raw.replace(" UTC", "").strip(), "%Y-%m-%d %H:%M"
        )
        built_utc = naive.replace(tzinfo=datetime.timezone.utc)
        local = timezone.localtime(built_utc)
        return local.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return raw


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
