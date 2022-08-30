# -*- coding: utf-8 -*-
import pytz

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from rest_framework.authtoken.models import Token


class Settings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dashboard_refresh_rate = models.DurationField(
        verbose_name=_("Refresh rate"),
        help_text=_(
            "If supported by browser, the dashboard will only refresh "
            "when visible, and also when receiving focus."
        ),
        blank=True,
        null=True,
        default=timezone.timedelta(minutes=1),
        choices=[
            (None, _("disabled")),
            (timezone.timedelta(minutes=1), _("1 min.")),
            (timezone.timedelta(minutes=2), _("2 min.")),
            (timezone.timedelta(minutes=3), _("3 min.")),
            (timezone.timedelta(minutes=4), _("4 min.")),
            (timezone.timedelta(minutes=5), _("5 min.")),
            (timezone.timedelta(minutes=10), _("10 min.")),
            (timezone.timedelta(minutes=15), _("15 min.")),
            (timezone.timedelta(minutes=30), _("30 min.")),
        ],
    )
    dashboard_hide_empty = models.BooleanField(
        verbose_name=_("Hide Empty Dashboard Cards"), default=False, editable=True
    )
    dashboard_hide_age = models.DurationField(
        verbose_name=_("Hide data older than"),
        help_text=_(
            "This setting controls which data will be shown " "in the dashboard."
        ),
        blank=True,
        null=True,
        default=None,
        choices=[
            (None, _("show all data")),
            (timezone.timedelta(days=1), _("1 day")),
            (timezone.timedelta(days=2), _("2 days")),
            (timezone.timedelta(days=3), _("3 days")),
            (timezone.timedelta(weeks=1), _("1 week")),
            (timezone.timedelta(weeks=4), _("4 weeks")),
        ],
    )
    language = models.CharField(
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        max_length=255,
        verbose_name=_("Language"),
    )
    timezone = models.CharField(
        choices=tuple(zip(pytz.common_timezones, pytz.common_timezones)),
        default=timezone.get_default_timezone_name(),
        max_length=100,
        verbose_name=_("Timezone"),
    )

    def __str__(self):
        return str(format_lazy(_("{user}'s Settings"), user=self.user))

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
