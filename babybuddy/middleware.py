from os import getenv
from time import time
from functools import wraps

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
                timezone.activate(user.settings.timezone)
            except ValueError:
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
    """
    Django middleware that adds HomeAssistant specific properties and checks
    to the request-object.

    The middleware is only active if the settings variable
    `ENABLE_HOME_ASSISTANT_SUPPORT` is set to True. Note that some features
    remain enabled even if the middleware is set to inactive through the
    settings.

    Features:

    - request.is_homeassistant_ingress_request (bool)

        Indicates if a request was rerouted through the home assistant ingress
        service. This parameters is always present regardless of the
        ENABLE_HOME_ASSISTANT_SUPPORT settings option. It defaults to false
        if the middleware is disabled.

    - wrapped request.build_absolute_uri function

        The middleware redefines (wraps) the build_absolute_uri function
        provided by django to allow it to interprete the X-Ingress-Path
        request header. This allows home assistant to construct correct
        absolute URLs when run through home assistant's ingress service.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.home_assistant_support_enabled = settings.ENABLE_HOME_ASSISTANT_SUPPORT

    def __wrap_build_absolute_uri(self, request: HttpRequest):
        def wrap_x_ingress_path(org_func):
            if not request.is_homeassistant_ingress_request:
                return org_func
            x_ingress_path = request.headers.get("X-Ingress-Path")
            if x_ingress_path is None:
                return org_func

            @wraps(org_func)
            def wrapper(*args, **kwargs):
                url = org_func(*args, **kwargs)
                url_parts = urlsplit(url)
                url = urlunsplit(
                    url_parts._replace(path=x_ingress_path + url_parts.path)
                )
                return url

            return wrapper

        request.build_absolute_uri = wrap_x_ingress_path(request.build_absolute_uri)

    def __call__(self, request: HttpRequest):
        if self.home_assistant_support_enabled:
            request.is_homeassistant_ingress_request = (
                request.headers.get("X-Hass-Source") == "core.ingress"
            )
        else:
            request.is_homeassistant_ingress_request = False

        self.__wrap_build_absolute_uri(request)

        return self.get_response(request)
