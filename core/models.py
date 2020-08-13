# -*- coding: utf-8 -*-
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _


def validate_date(date, field_name):
    """
    Confirm that a date is not in the future.
    :param date: a timezone aware date instance.
    :param field_name: the name of the field being checked.
    :return:
    """
    if date and date > timezone.localdate():
        raise ValidationError(
            {field_name: _('Date can not be in the future.')},
            code='date_invalid')


def validate_duration(model, max_duration=timedelta(hours=24)):
    """
    Basic sanity checks for models with a duration
    :param model: a model instance with 'start' and 'end' attributes
    :param max_duration: maximum allowed duration between start and end time
    :return:
    """
    if model.start and model.end:
        if model.start > model.end:
            raise ValidationError(
                _('Start time must come before end time.'),
                code='end_before_start')
        if model.end - model.start > max_duration:
            raise ValidationError(_('Duration too long.'), code='max_duration')


def validate_unique_period(queryset, model):
    """
    Confirm that model's start and end date do not intersect with other
    instances.
    :param queryset: a queryset of instances to check against.
    :param model: a model instance with 'start' and 'end' attributes
    :return:
    """
    if model.id:
        queryset = queryset.exclude(id=model.id)
    if model.start and model.end:
        if queryset.filter(start__lte=model.end, end__gte=model.start):
            raise ValidationError(
                _('Another entry intersects the specified time period.'),
                code='period_intersection')


def validate_time(time, field_name):
    """
    Confirm that a time is not in the future.
    :param time: a timezone aware datetime instance.
    :param field_name: the name of the field being checked.
    :return:
    """
    if time and time > timezone.localtime():
        raise ValidationError(
            {field_name: _('Date/time can not be in the future.')},
            code='time_invalid')


class Child(models.Model):
    model_name = 'child'
    first_name = models.CharField(max_length=255, verbose_name=_('First name'))
    last_name = models.CharField(max_length=255, verbose_name=_('Last name'))
    birth_date = models.DateField(
        blank=False,
        null=False,
        verbose_name=_('Birth date')
    )
    slug = models.SlugField(
        editable=False,
        max_length=100,
        unique=True,
        verbose_name=_('Slug')
    )
    picture = models.ImageField(
        blank=True,
        null=True,
        upload_to='child/picture/',
        verbose_name=_('Picture')
    )

    objects = models.Manager()

    cache_key_count = 'core.child.count'

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['last_name', 'first_name']
        verbose_name = _('Child')
        verbose_name_plural = _('Children')

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def save(self, *args, **kwargs):
        self.slug = slugify(self)
        super(Child, self).save(*args, **kwargs)
        cache.set(self.cache_key_count, Child.objects.count(), None)

    def delete(self, using=None, keep_parents=False):
        super(Child, self).delete(using, keep_parents)
        cache.set(self.cache_key_count, Child.objects.count(), None)

    def name(self, reverse=False):
        if reverse:
            return '{}, {}'.format(self.last_name, self.first_name)

        return '{} {}'.format(self.first_name, self.last_name)

    @classmethod
    def count(cls):
        """ Get a (cached) count of total number of Child instances. """
        return cache.get_or_set(cls.cache_key_count, Child.objects.count, None)


class DiaperChange(models.Model):
    model_name = 'diaperchange'
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
        related_name='diaper_change',
        verbose_name=_('Child')
    )
    time = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_('Time')
    )
    wet = models.BooleanField(verbose_name=_('Wet'))
    solid = models.BooleanField(verbose_name=_('Solid'))
    color = models.CharField(
        blank=True,
        choices=[
            ('black', _('Black')),
            ('brown', _('Brown')),
            ('green', _('Green')),
            ('yellow', _('Yellow')),
        ],
        max_length=255,
        verbose_name=_('Color')
    )
    amount = models.FloatField(blank=True, null=True, verbose_name=_('Amount'))
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-time']
        verbose_name = _('Diaper Change')
        verbose_name_plural = _('Diaper Changes')

    def __str__(self):
        return str(_('Diaper Change'))

    def attributes(self):
        attributes = []
        if self.wet:
            attributes.append(self._meta.get_field('wet').verbose_name)
        if self.solid:
            attributes.append(self._meta.get_field('solid').verbose_name)
        if self.color:
            attributes.append(self.get_color_display())
        return attributes

    def clean(self):
        validate_time(self.time, 'time')

        # One or both of Wet and Solid is required.
        if not self.wet and not self.solid:
            raise ValidationError(
                _('Wet and/or solid is required.'), code='wet_or_solid')


class Feeding(models.Model):
    model_name = 'feeding'
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
        related_name='feeding',
        verbose_name=_('Child')
    )
    start = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_('Start time')
    )
    end = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_('End time')
    )
    duration = models.DurationField(
        editable=False,
        null=True,
        verbose_name=_('Duration')
    )
    type = models.CharField(
        choices=[
            ('breast milk', _('Breast milk')),
            ('formula', _('Formula')),
            ('fortified breast milk', _('Fortified breast milk')),
        ],
        max_length=255,
        verbose_name=_('Type')
    )
    method = models.CharField(
        choices=[
            ('bottle', _('Bottle')),
            ('left breast', _('Left breast')),
            ('right breast', _('Right breast')),
            ('both breasts', _('Both breasts')),
        ],
        max_length=255,
        verbose_name=_('Method')
    )
    amount = models.FloatField(blank=True, null=True, verbose_name=_('Amount'))
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']
        verbose_name = _('Feeding')
        verbose_name_plural = _('Feedings')

    def __str__(self):
        return str(_('Feeding'))

    def save(self, *args, **kwargs):
        if self.start and self.end:
            self.duration = self.end - self.start
        super(Feeding, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, 'start')
        validate_time(self.end, 'end')
        validate_duration(self)
        validate_unique_period(Feeding.objects.filter(child=self.child), self)


class Note(models.Model):
    model_name = 'note'
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
        related_name='note',
        verbose_name=_('Child')
    )
    note = models.TextField(verbose_name=_('Note'))
    time = models.DateTimeField(
        default=timezone.now,
        blank=False,
        verbose_name=_('Time')
    )

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-time']
        verbose_name = _('Note')
        verbose_name_plural = _('Notes')

    def __str__(self):
        return str(_('Note'))


class NapsManager(models.Manager):
    def get_queryset(self):
        qs = super(NapsManager, self).get_queryset()
        return qs.filter(id__in=[obj.id for obj in qs if obj.nap])


class Sleep(models.Model):
    model_name = 'sleep'
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
        related_name='sleep',
        verbose_name=_('Child')
    )
    start = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_('Start time')
    )
    end = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_('End time')
    )
    duration = models.DurationField(
        editable=False,
        null=True,
        verbose_name=_('Duration')
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))

    objects = models.Manager()
    naps = NapsManager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']
        verbose_name = _('Sleep')
        verbose_name_plural = _('Sleep')

    def __str__(self):
        return str(_('Sleep'))

    @property
    def nap(self):
        nap_start_min = timezone.datetime.strptime(
            settings.BABY_BUDDY['NAP_START_MIN'], '%H:%M').time()
        nap_start_max = timezone.datetime.strptime(
            settings.BABY_BUDDY['NAP_START_MAX'], '%H:%M').time()
        local_start_time = timezone.localtime(self.start).time()
        return nap_start_min <= local_start_time <= nap_start_max

    def save(self, *args, **kwargs):
        if self.start and self.end:
            self.duration = self.end - self.start
        super(Sleep, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, 'start')
        validate_time(self.end, 'end')
        validate_duration(self)
        validate_unique_period(Sleep.objects.filter(child=self.child), self)


class Temperature(models.Model):
    model_name = 'temperature'
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
        related_name='temperature',
        verbose_name=_('Child')
    )
    temperature = models.FloatField(
        blank=False,
        null=False,
        verbose_name=_('Temperature')
    )
    time = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_('Time')
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-time']
        verbose_name = _('Temperature')
        verbose_name_plural = _('Temperature')

    def __str__(self):
        return str(_('Temperature'))

    def clean(self):
        validate_time(self.time, 'time')


class Timer(models.Model):
    model_name = 'timer'
    child = models.ForeignKey(
        'Child',
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='timers',
        verbose_name=_('Child')
    )
    name = models.CharField(
        blank=True,
        max_length=255,
        null=True,
        verbose_name=_('Name')
    )
    start = models.DateTimeField(
        default=timezone.now,
        blank=False,
        verbose_name=_('Start time')
    )
    end = models.DateTimeField(
        blank=True,
        editable=False,
        null=True,
        verbose_name=_('End time')
    )
    duration = models.DurationField(
        editable=False,
        null=True,
        verbose_name=_('Duration')
    )
    active = models.BooleanField(
        default=True,
        editable=False,
        verbose_name=_('Active')
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='timers',
        verbose_name=_('User')
    )

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-active', '-start', '-end']
        verbose_name = _('Timer')
        verbose_name_plural = _('Timers')

    def __str__(self):
        return self.name or str(format_lazy(_('Timer #{id}'), id=self.id))

    @property
    def title_with_child(self):
        """ Get Timer title with child name in parenthesis. """
        title = str(self)
        # Only actually add the name if there is more than one Child instance.
        if title and self.child and Child.count() > 1:
            title = format_lazy('{title} ({child})', title=title,
                                child=self.child)
        return title

    @property
    def user_username(self):
        """ Get Timer user's name with a preference for the full name. """
        if self.user.get_full_name():
            return self.user.get_full_name()
        return self.user.get_username()

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super(Timer, cls).from_db(db, field_names, values)
        if not instance.duration:
            instance.duration = timezone.now() - instance.start
        return instance

    def restart(self):
        """Restart the timer."""
        self.start = timezone.now()
        self.end = None
        self.duration = None
        self.active = True
        self.save()

    def stop(self, end=None):
        """Stop the timer."""
        if not end:
            end = timezone.now()
        self.end = end
        self.save()

    def save(self, *args, **kwargs):
        self.active = self.end is None
        self.name = self.name or None
        if self.start and self.end:
            self.duration = self.end - self.start
        else:
            self.duration = None
        super(Timer, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, 'start')
        if self.end:
            validate_time(self.end, 'end')
        validate_duration(self)


class TummyTime(models.Model):
    model_name = 'tummytime'
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
        related_name='tummy_time',
        verbose_name=_('Child')
    )
    start = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_('Start time')
    )
    end = models.DateTimeField(
        blank=False,
        null=False,
        verbose_name=_('End time')
    )
    duration = models.DurationField(
        editable=False,
        null=True,
        verbose_name=_('Duration')
    )
    milestone = models.CharField(
        blank=True,
        max_length=255,
        verbose_name=_('Milestone')
    )

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-start']
        verbose_name = _('Tummy Time')
        verbose_name_plural = _('Tummy Time')

    def __str__(self):
        return str(_('Tummy Time'))

    def save(self, *args, **kwargs):
        if self.start and self.end:
            self.duration = self.end - self.start
        super(TummyTime, self).save(*args, **kwargs)

    def clean(self):
        validate_time(self.start, 'start')
        validate_time(self.end, 'end')
        validate_duration(self)
        validate_unique_period(
            TummyTime.objects.filter(child=self.child), self)


class Weight(models.Model):
    model_name = 'weight'
    child = models.ForeignKey(
        'Child',
        on_delete=models.CASCADE,
        related_name='weight',
        verbose_name=_('Child')
    )
    weight = models.FloatField(
        blank=False,
        null=False,
        verbose_name=_('Weight')
    )
    date = models.DateField(
        blank=False,
        null=False,
        verbose_name=_('Date')
    )
    notes = models.TextField(blank=True, null=True, verbose_name=_('Notes'))

    objects = models.Manager()

    class Meta:
        default_permissions = ('view', 'add', 'change', 'delete')
        ordering = ['-date']
        verbose_name = _('Weight')
        verbose_name_plural = _('Weight')

    def __str__(self):
        return str(_('Weight'))

    def clean(self):
        validate_date(self.date, 'date')
