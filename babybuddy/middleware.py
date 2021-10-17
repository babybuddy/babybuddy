import time

import pytz

from django.conf import settings
from django.utils import timezone


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
        if hasattr(request.user, 'settings') and request.user.settings.timezone:
            try:
                timezone.activate(pytz.timezone(request.user.settings.timezone))
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
