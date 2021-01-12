import time

import pytz

from django.conf import settings
from django.utils import timezone


class UserTimezoneMiddleware:
    """
    Sets the timezone based on a user specific setting that falls back on
    `settings.TIME_ZONE`.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone_name = request.session.get('user_timezone')
        if timezone_name:
            try:
                timezone.activate(pytz.timezone(timezone_name))
            except pytz.UnknownTimeZoneError:
                pass
        return self.get_response(request)


class RollingSessionMiddleware:
    """
    Periodically resets the session expiry.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_refresh = request.session.get('session_refresh')
        if session_refresh:
            try:
                delta = int(time.time()) - session_refresh
            except (ValueError, TypeError):
                delta = settings.ROLLING_SESSION_REFRESH + 1
            if delta > settings.ROLLING_SESSION_REFRESH:
                request.session['session_refresh'] = int(time.time())
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        else:
            request.session['session_refresh'] = int(time.time())
        return self.get_response(request)
