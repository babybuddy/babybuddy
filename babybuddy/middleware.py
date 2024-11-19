import logging
from os import getenv
from time import time
from functools import wraps

from urllib.parse import urlunsplit, urlsplit

from django.conf import settings
from django.utils import timezone, translation
from django.contrib.auth.middleware import RemoteUserMiddleware
from django.http import (
    HttpRequest,
    HttpResponseRedirect,
    HttpResponse,
    StreamingHttpResponse,
)
from django.urls.base import set_script_prefix, get_script_prefix


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

    def process_request(self, request):
        # Exclude API paths using token authentication.
        if request.path.startswith("api/"):
            return None
        return super().process_request(request)


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
        self.original_script_prefix = get_script_prefix()

    def __call__(self, request: HttpRequest):
        if self.home_assistant_support_enabled:
            request.is_homeassistant_ingress_request = (
                request.headers.get("X-Hass-Source") == "core.ingress"
            )
        else:
            request.is_homeassistant_ingress_request = False
            return self.get_response(request)

        apply_x_ingress_path = True
        if not request.is_homeassistant_ingress_request:
            apply_x_ingress_path = False
        x_ingress_path = request.headers.get("X-Ingress-Path")
        if x_ingress_path is None:
            apply_x_ingress_path = False

        if apply_x_ingress_path:
            set_script_prefix("/" + x_ingress_path.lstrip("/"))
        else:
            set_script_prefix(self.original_script_prefix)

        response = self.get_response(request)

        if apply_x_ingress_path:
            is_redirect_response = isinstance(
                response, HttpResponseRedirect
            ) or response.status_code in [301, 307, 308]
            if is_redirect_response:
                split_url = urlsplit(response["Location"])
                path_prefix = "/" + x_ingress_path.lstrip("/")
                if not split_url.path.startswith(path_prefix):
                    new_url = urlunsplit(
                        (
                            split_url.scheme,
                            split_url.netloc,
                            "/" + x_ingress_path.lstrip("/") + split_url.path,
                            split_url.query,
                            split_url.fragment,
                        )
                    )
                    response["Location"] = new_url
            elif isinstance(response, StreamingHttpResponse):
                # Pray that the response works
                logging.error(
                    "HomeAssistant middleware: StreamingHttpResponse is not "
                    "supported. Resulting URLs to home assistant ingress might "
                    "be incorrect."
                )
            elif isinstance(response, HttpResponse):
                if response["Content-Type"].lower().startswith("text/html"):
                    # Filter /static and /media URLs, I did not find a better
                    # way that would be compatible with external third-party apps.
                    content = response.content.decode()
                    static_trunc = settings.STATIC_URL.rstrip("/")
                    media_trunc = settings.MEDIA_URL.rstrip("/")

                    content = (
                        content.replace(
                            f'"{static_trunc}',
                            f'"{x_ingress_path}{static_trunc}',
                        )
                        .replace(
                            f"'{static_trunc}",
                            f"'{x_ingress_path}{static_trunc}",
                        )
                        .replace(
                            f'"{media_trunc}',
                            f'"{x_ingress_path}{media_trunc}',
                        )
                        .replace(
                            f"'{media_trunc}",
                            f"'{x_ingress_path}{media_trunc}",
                        )
                    )
                    filtered_headers = {
                        key: value
                        for key, value in response.headers.items()
                        if not key.lower().startswith("content-")
                    }
                    response = HttpResponse(
                        content.encode(),
                        status=response.status_code,
                        content_type=response["Content-Type"],
                        charset=response.charset,
                        headers=filtered_headers,
                    )

        return response
