from os import getenv
from time import time

import pytz

from django.conf import settings
from django.utils import timezone, translation
from django.conf.locale.en import formats as formats_en_us
from django.conf.locale.en_GB import formats as formats_en_gb
from django.contrib.auth.middleware import RemoteUserMiddleware


def update_en_us_date_formats():
    """
    Update the datetime formats for the en-US locale. This is handled here and
    not using `FORMAT_MODULE_PATH` because the processing of format modules
    does not allow us to distinguish appropriately between en-US and en-GB
    based on user settings.
    """
    if settings.USE_24_HOUR_TIME_FORMAT:
        formats_en_us.DATETIME_FORMAT = "N j, Y, H:i:s"
        custom_input_formats = [
            "%m/%d/%Y %H:%M:%S",  # '10/25/2006 14:30:59'
            "%m/%d/%Y %H:%M",  # '10/25/2006 14:30'
        ]
        formats_en_us.SHORT_DATETIME_FORMAT = "m/d/Y G:i:s"
        formats_en_us.TIME_FORMAT = "H:i:s"
    else:
        # These formats are added to support the locale style of Baby Buddy's
        # frontend library, which uses momentjs.
        custom_input_formats = [
            "%m/%d/%Y %I:%M:%S %p",  # '10/25/2006 2:30:59 PM'
            "%m/%d/%Y %I:%M %p",  # '10/25/2006 2:30 PM'
        ]

    # Add custom "short" version of `MONTH_DAY_FORMAT`.
    formats_en_us.SHORT_MONTH_DAY_FORMAT = "M j"

    # Append all other input formats from the base locale.
    formats_en_us.DATETIME_INPUT_FORMATS = (
        custom_input_formats + formats_en_us.DATETIME_INPUT_FORMATS
    )


def update_en_gb_date_formats():
    if settings.USE_24_HOUR_TIME_FORMAT:
        # 25 October 2006 14:30:00
        formats_en_gb.DATETIME_FORMAT = "j F Y H:i:s"
        custom_input_formats = [
            "%d/%m/%Y %H:%M:%S",  # '25/10/2006 14:30:59'
            "%d/%m/%Y %H:%M",  # '25/10/2006 14:30'
        ]
        formats_en_gb.SHORT_DATETIME_FORMAT = "d/m/Y H:i"
        formats_en_gb.TIME_FORMAT = "H:i"
    else:
        formats_en_gb.DATETIME_FORMAT = "j F Y f a"  # 25 October 2006 2:30 p.m
        # These formats are added to support the locale style of Baby Buddy's
        # frontend library, which uses momentjs.
        custom_input_formats = [
            "%d/%m/%Y %I:%M:%S %p",  # '25/10/2006 2:30:59 PM'
            "%d/%m/%Y %I:%M %p",  # '25/10/2006 2:30 PM'
        ]

    # Append all other input formats from the base locale.
    formats_en_gb.DATETIME_INPUT_FORMATS = (
        custom_input_formats + formats_en_gb.DATETIME_INPUT_FORMATS
    )


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
            if language == "en-US":
                update_en_us_date_formats()
            elif language == "en-GB":
                update_en_gb_date_formats()

            # Set the language before generating the response.
            translation.activate(language)

        response = self.get_response(request)

        # Deactivate the translation before the response is sent so it not
        # reused in other threads.
        translation.deactivate()

        return response


class UserTimezoneMiddleware:
    """
    Sets the timezone based on a user specific setting that falls back on
    `settings.TIME_ZONE`. This middleware must run after
    `django.contrib.auth.middleware.AuthenticationMiddleware` because it uses
    the request.user object.
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
