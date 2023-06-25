from os import getenv
from time import time

import pytz
from urllib.parse import urlunsplit, urlsplit

from django.conf import settings
from django.utils import timezone, translation
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.http import HttpRequest


class UserLanguageMiddleware:
    """
    Customizes settings based on user language setting.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if hasattr(user, "settings") and user.settings.language:
            language = user.settings.language
        elif request.LANGUAGE_CODE:
            language = request.LANGUAGE_CODE
        else:
            language = settings.LANGUAGE_CODE

        if language:
            # Set the language before generating the response.
            translation.activate(language)

        response = self.get_response(request)

        # Deactivate the translation before the response is sent so it not
        # reused in other threads.
        translation.deactivate()

        return response


class UserTimezoneMiddleware:
    """
    Sets the timezone based on a user specific setting. This middleware must run after
    `django.contrib.auth.middleware.AuthenticationMiddleware` because it uses the
    request.user object.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if hasattr(user, "settings") and user.settings.timezone:
            try:
                timezone.activate(pytz.timezone(user.settings.timezone))
            except pytz.UnknownTimeZoneError:
                pass
        return self.get_response(request)


class RollingSessionMiddleware:
    """
    Periodically resets the session expiry for existing sessions.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.session.keys():
            session_refresh = request.session.get("session_refresh")
            if session_refresh:
                try:
                    delta = int(time()) - session_refresh
                except (ValueError, TypeError):
                    delta = settings.ROLLING_SESSION_REFRESH + 1
                if delta > settings.ROLLING_SESSION_REFRESH:
                    request.session["session_refresh"] = int(time())
                    request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            else:
                request.session["session_refresh"] = int(time())
        return self.get_response(request)


class CustomRemoteUser(RemoteUserMiddleware):
    """
    Middleware used for remote authentication when `REVERSE_PROXY_AUTH` is True.
    """

    header = getenv("PROXY_HEADER", "HTTP_REMOTE_USER")


class HomeAssistant:
    def __init__(self, get_response):
        self.get_response = get_response
        self.use_x_ingress_path_rewrite = settings.HOME_ASSISTANT_USE_X_INGRESS_PATH

    def __call__(self, request: HttpRequest):
        def wrap_x_ingress_path(org_func):
            if not request.is_homeassistant_ingress_request:
                return org_func
            x_ingress_path = request.headers.get("X-Ingress-Path")
            if x_ingress_path is None:
                return org_func

            def wrapper(*args, **kwargs):
                url = org_func(*args, **kwargs)

                url_parts = urlsplit(url)
                url = urlunsplit(
                    url_parts._replace(path=x_ingress_path + url_parts.path)
                )

                return url

            return wrapper

        request.is_homeassistant_ingress_request = (
            request.headers.get("X-Hass-Source") == "core.ingress"
        )

        if self.use_x_ingress_path_rewrite:
            request.build_absolute_uri = wrap_x_ingress_path(request.build_absolute_uri)

        return self.get_response(request)
