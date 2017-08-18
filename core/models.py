# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone, timesince

from .utils import duration_string


class Child(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    birth_date = models.DateField(blank=False, null=False)
    slug = models.SlugField(max_length=100, unique=True, editable=False)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'Children'

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        self.slug = slugify(self)
        super(Child, self).save(*args, **kwargs)


class DiaperChange(models.Model):
    child = models.ForeignKey('Child', related_name='diaper_change')
    time = models.DateTimeField(blank=False, null=False)
    wet = models.BooleanField()
    solid = models.BooleanField()
    color = models.CharField(max_length=255, blank=True, choices=[
        ('black', 'Black'),
        ('brown', 'Brown'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
    ])

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-time']

    def __str__(self):
        return 'Diaper change for {} on {}'.format(
            self.child, self.time.date())

    def since(self, time=timezone.now()):
        return timesince.timesince(self.time, time)

    def attributes(self):
        attributes = []
        if self.wet:
            attributes.append(DiaperChange._meta.get_field('wet').name)
        if self.solid:
            attributes.append(DiaperChange._meta.get_field('solid').name)
        if self.color:
            attributes.append(self.color)
        return attributes


class Feeding(models.Model):
    child = models.ForeignKey('Child', related_name='feeding')
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
    amount = models.FloatField(blank=True, null=True)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']

    def __str__(self):
        return 'Feeding for {} on {} ({})'.format(
            self.child, self.end.date(), self.duration())

    def duration(self):
        return duration_string(self.start, self.end)

    def since(self, time=timezone.now()):
        return timesince.timesince(self.end, time)


class Note(models.Model):
    child = models.ForeignKey('Child', related_name='note')
    note = models.TextField()
    time = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-time']

    def __str__(self):
        return 'Note about {} on {}'.format(self.child, self.time.date())

    def since(self, time=timezone.now()):
        return timesince.timesince(self.time, time)


class Sleep(models.Model):
    child = models.ForeignKey('Child', related_name='sleep')
    start = models.DateTimeField(blank=False, null=False)
    end = models.DateTimeField(blank=False, null=False)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']
        verbose_name_plural = 'Sleep'

    def __str__(self):
        return 'Sleep for {} on {} ({})'.format(
            self.child, self.end.date(), self.duration())

    def duration(self):
        return duration_string(self.start, self.end)

    def since(self, time=timezone.now()):
        return timesince.timesince(self.end, time)


class Timer(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)
    start = models.DateTimeField(auto_now_add=True)
    end = models.DateTimeField(blank=True, null=True, editable=False)
    active = models.BooleanField(default=True, editable=False)
    user = models.ForeignKey('auth.User', related_name='timers')

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-active', '-start', '-end']

    def __str__(self):
        return self.name or 'Timer #{}'.format(self.id)

    def duration(self):
        return duration_string(self.start, self.end or timezone.now(),
                               short=True)

    def save(self, *args, **kwargs):
        self.active = self.end is None
        self.name = self.name or None
        super(Timer, self).save(*args, **kwargs)


class TummyTime(models.Model):
    child = models.ForeignKey('Child', related_name='tummy_time')
    start = models.DateTimeField(blank=False, null=False)
    end = models.DateTimeField(blank=False, null=False)
    milestone = models.CharField(max_length=255, blank=True)

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']

    def __str__(self):
        return 'Tummy time for {} on {} ({})'.format(
            self.child, self.end.date(), self.duration())

    def duration(self):
        return duration_string(self.start, self.end)

    def since(self, time=timezone.now()):
        return timesince.timesince(self.end, time)
