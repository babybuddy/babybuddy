# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import timedelta
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
        default=timedelta(minutes=1),
        choices=[
            (None, _('disabled')),
            (timedelta(minutes=1), _('1 min.')),
            (timedelta(minutes=2), _('2 min.')),
            (timedelta(minutes=3), _('3 min.')),
            (timedelta(minutes=4), _('4 min.')),
            (timedelta(minutes=5), _('5 min.')),
            (timedelta(minutes=10), _('10 min.')),
            (timedelta(minutes=15), _('15 min.')),
            (timedelta(minutes=30), _('30 min.')),
        ])

    def __str__(self):
        return '{}\'s Settings'.format(self.user)

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
