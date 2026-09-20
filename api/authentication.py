from django.utils.translation import gettext_lazy as _
from rest_framework import authentication, exceptions

from babybuddy.models import access_expired


class TokenAuthentication(authentication.TokenAuthentication):
    """
    Token authentication that also refuses users whose access has expired.
    """

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if access_expired(user):
            raise exceptions.AuthenticationFailed(_("Your access has expired."))
        return user, token
