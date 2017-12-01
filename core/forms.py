# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils import timezone
from django.conf import settings

from core import models


# Sets the default Child instance if only one exists in the database.
def set_default_child(kwargs):
    instance = kwargs.get('instance', None)
    if not kwargs.get('initial'):
        kwargs.update(initial={})
    if instance is None and models.Child.objects.count() == 1:
        kwargs['initial'].update({'child': models.Child.objects.first()})
    return kwargs


# Uses a timer to set the default start and end date and updates the timer.
def set_default_duration(kwargs):
    instance = kwargs.get('instance', None)
    timer_id = kwargs.get('timer', None)
    if not kwargs.get('initial'):
        kwargs.update(initial={})
    if not instance and timer_id:
        instance = models.Timer.objects.get(id=timer_id)
        kwargs['initial'].update({
            'timer': instance,
            'start': instance.start,
            'end': instance.end or timezone.now()
        })
    try:
        kwargs.pop('timer')
    except KeyError:
        pass
    return kwargs


class ChildForm(forms.ModelForm):
    class Meta:
        model = models.Child
        fields = [
            'first_name',
            'last_name',
            'birth_date'
        ]
        if settings.BABY_BUDDY['ALLOW_UPLOADS']:
            fields.append('picture')
        widgets = {
            'birth_date': forms.DateInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_date',
            }),
        }


class ChildDeleteForm(forms.ModelForm):
    confirm_name = forms.CharField(max_length=511)

    class Meta:
        model = models.Child
        fields = []

    def clean_confirm_name(self):
        confirm_name = self.cleaned_data['confirm_name']
        if confirm_name != str(self.instance):
            raise forms.ValidationError(
                'Name does not match child name.', code='confirm_mismatch')
        return confirm_name

    def save(self, commit=True):
        instance = self.instance
        self.instance.delete()
        return instance


class DiaperChangeForm(forms.ModelForm):
    class Meta:
        model = models.DiaperChange
        fields = ['child', 'time', 'wet', 'solid', 'color']
        widgets = {
            'time': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_time',
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs = set_default_child(kwargs)
        super(DiaperChangeForm, self).__init__(*args, **kwargs)


class FeedingForm(forms.ModelForm):
    class Meta:
        model = models.Feeding
        fields = ['child', 'start', 'end', 'type', 'method', 'amount']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_end',
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs = set_default_child(kwargs)
        self.timer_id = kwargs.get('timer', None)
        kwargs = set_default_duration(kwargs)
        super(FeedingForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(FeedingForm, self).save(commit=False)
        if self.timer_id:
            timer = models.Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        instance.save()
        return instance


class NoteForm(forms.ModelForm):
    class Meta:
        model = models.Note
        fields = ['child', 'note']

    def __init__(self, *args, **kwargs):
        kwargs = set_default_child(kwargs)
        super(NoteForm, self).__init__(*args, **kwargs)


class SleepForm(forms.ModelForm):
    class Meta:
        model = models.Sleep
        fields = ['child', 'start', 'end']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_end',
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs = set_default_child(kwargs)
        self.timer_id = kwargs.get('timer', None)
        kwargs = set_default_duration(kwargs)
        super(SleepForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(SleepForm, self).save(commit=False)
        if self.timer_id:
            timer = models.Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        instance.save()
        return instance


class TimerForm(forms.ModelForm):
    class Meta:
        model = models.Timer
        fields = ['name', 'start']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_start',
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(TimerForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TimerForm, self).save(commit=False)
        instance.user = self.user
        instance.save()
        return instance


class TummyTimeForm(forms.ModelForm):
    class Meta:
        model = models.TummyTime
        fields = ['child', 'start', 'end', 'milestone']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_end',
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs = set_default_child(kwargs)
        self.timer_id = kwargs.get('timer', None)
        kwargs = set_default_duration(kwargs)
        super(TummyTimeForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TummyTimeForm, self).save(commit=False)
        if self.timer_id:
            timer = models.Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        instance.save()
        return instance


class WeightForm(forms.ModelForm):
    class Meta:
        model = models.Weight
        fields = ['child', 'weight', 'date']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'datepicker-input',
                'data-target': '#datetimepicker_date',
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs = set_default_child(kwargs)
        super(WeightForm, self).__init__(*args, **kwargs)
