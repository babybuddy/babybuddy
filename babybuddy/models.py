# -*- coding: utf-8 -*-
import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone, translation
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from rest_framework.authtoken.models import Token


class Settings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dashboard_refresh_rate = models.DurationField(
        verbose_name=_('Refresh rate'),
        help_text=_('This setting will only be used when a browser does not '
                    'support refresh on focus.'),
        blank=True,
        null=True,
        default=timezone.timedelta(minutes=1),
        choices=[
            (None, _('disabled')),
            (timezone.timedelta(minutes=1), _('1 min.')),
            (timezone.timedelta(minutes=2), _('2 min.')),
            (timezone.timedelta(minutes=3), _('3 min.')),
            (timezone.timedelta(minutes=4), _('4 min.')),
            (timezone.timedelta(minutes=5), _('5 min.')),
            (timezone.timedelta(minutes=10), _('10 min.')),
            (timezone.timedelta(minutes=15), _('15 min.')),
            (timezone.timedelta(minutes=30), _('30 min.')),
        ])
    language = models.CharField(
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        max_length=255,
        verbose_name=_('Language')
    )
    timezone = models.CharField(
        choices=tuple(zip(pytz.common_timezones, pytz.common_timezones)),
        default=timezone.get_default_timezone_name(),
        max_length=100,
        verbose_name=_('Timezone')
    )

    def __str__(self):
        return str(format_lazy(_('{user}\'s Settings'), user=self.user))

    def api_key(self, reset=False):
        """
        Get or create an API key for the associated user.
        :param reset: If True, delete the existing key and create a new one.
        :return: The user's API key.
        """
        if reset:
            Token.objects.get(user=self.user).delete()
        return Token.objects.get_or_create(user=self.user)[0]

    @property
    def dashboard_refresh_rate_milliseconds(self):
        """
        Convert seconds to milliseconds to be used in a Javascript setInterval
        function call.
        :return: the refresh rate in milliseconds or None.
        """
        if self.dashboard_refresh_rate:
            return self.dashboard_refresh_rate.seconds * 1000
        return None


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    if created:
        Settings.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_settings(sender, instance, **kwargs):
    instance.settings.save()


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    if user.settings.language:
        translation.activate(user.settings.language)
        # TODO: Change this behavior as session-based language is deprecated.
        request.session[
            translation.LANGUAGE_SESSION_KEY] = user.settings.language
    if user.settings.timezone:
        timezone.activate(user.settings.timezone)
        request.session['user_timezone'] = user.settings.timezone
