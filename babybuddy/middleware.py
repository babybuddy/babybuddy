import pytz

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
