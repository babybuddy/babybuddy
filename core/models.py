# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
from math import floor

from django.db import models


class Baby(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birth_date = models.DateField(blank=False, null=False)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Babies'

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Sleep(models.Model):
    baby = models.ForeignKey('Baby', related_name='sleep')
    start = models.DateTimeField(blank=False, null=False)
    end = models.DateTimeField(blank=False, null=False)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']
        verbose_name_plural = 'Sleep'

    def __str__(self):
        return '{} slept for {}'.format(
            self.baby,
            self.duration()
        )

    def duration(self):
        diff = self.end - self.start
        if diff.seconds < 60:
            duration = '{} second{}'.format(
                diff.seconds,
                's' if diff.seconds > 1 else ''
            )
        elif diff.seconds < 3600:
            duration = '{} minute{}, {} second{}'.format(
                floor(diff.seconds / 60),
                's' if floor(diff.seconds / 60) > 1 else '',
                diff.seconds % 60,
                's' if diff.seconds % 60 > 1 else ''
            )
        else:
            duration = '{} hour{}, {} minute{}, {} second{}'.format(
                floor(diff.seconds / 3600),
                's' if floor(diff.seconds / 3600) > 1 else '',
                floor((diff.seconds - 3600) / 60),
                's' if floor((diff.seconds - 3600) / 60) > 1 else '',
                diff.seconds % 60,
                's' if diff.seconds % 60 > 1 else ''
            )
        return duration
