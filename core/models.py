# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from .utils import duration_string


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


class Feeding(models.Model):
    baby = models.ForeignKey('Baby', related_name='feeding')
    start = models.DateTimeField(blank=False, null=False)
    end = models.DateTimeField(blank=False, null=False)
    type = models.CharField(max_length=255, choices=[
        ('breast milk', 'Breast milk'),
        ('formula', 'Formula'),
    ])
    method = models.CharField(max_length=255, choices=[
        ('bottle', 'Bottle'),
        ('left breast', 'Left breast'),
        ('right breast', 'Right breast'),
    ])

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']

    def __str__(self):
        return 'Feeding for {} on {} ({})'.format(
            self.baby, self.end.date(), self.duration())

    def duration(self):
        return duration_string(self.start, self.end)


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
        return 'Sleep for {} on {} ({})'.format(
            self.baby, self.end.date(), self.duration())

    def duration(self):
        return duration_string(self.start, self.end)
