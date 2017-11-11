# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import timedelta


class Settings(models.Model):
    user = models.OneToOneField(User)
    dashboard_refresh_rate = models.DurationField(
        verbose_name='Refresh rate',
        blank=True,
        null=True,
        default=timedelta(minutes=1),
        choices=[
            (None, 'disabled'),
            (timedelta(minutes=1), '1 min.'),
            (timedelta(minutes=2), '2 min.'),
            (timedelta(minutes=3), '3 min.'),
            (timedelta(minutes=4), '4 min.'),
            (timedelta(minutes=5), '5 min.'),
            (timedelta(minutes=10), '10 min.'),
            (timedelta(minutes=15), '15 min.'),
            (timedelta(minutes=30), '30 min.'),
        ])

    def __str__(self):
        return '{}\'s Settings'.format(self.user)

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
