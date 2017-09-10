# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.utils import timezone

from .models import Child, DiaperChange, Feeding, Sleep, Timer, TummyTime


# Sets the default Child instance if only one exists in the database.
def set_default_child(kwargs):
    instance = kwargs.get('instance', None)
    if not kwargs.get('initial'):
        kwargs.update(initial={})
    if instance is None and Child.objects.count() == 1:
        kwargs['initial'].update({'child': Child.objects.first()})
    return kwargs


# Uses a timer to set the default start and end date and updates the timer.
def set_default_duration(kwargs):
    instance = kwargs.get('instance', None)
    timer_id = kwargs.get('timer', None)
    if not kwargs.get('initial'):
        kwargs.update(initial={})
    if not instance and timer_id:
        instance = Timer.objects.get(id=timer_id)
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
        model = Child
        fields = ['first_name', 'last_name', 'birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_birth_date',
            }),
        }


class DiaperChangeForm(forms.ModelForm):
    class Meta:
        model = DiaperChange
        fields = ['child', 'time', 'wet', 'solid', 'color']
        widgets = {
            'time': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_time',
            }),
        }

    def __init__(self, *args, **kwargs):
        kwargs = set_default_child(kwargs)
        super(DiaperChangeForm, self).__init__(*args, **kwargs)


class FeedingForm(forms.ModelForm):
    class Meta:
        model = Feeding
        fields = ['child', 'start', 'end', 'type', 'method', 'amount']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_end',
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
            timer = Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        instance.save()
        return instance


class SleepForm(forms.ModelForm):
    class Meta:
        model = Sleep
        fields = ['child', 'start', 'end']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_end',
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
            timer = Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        instance.save()
        return instance


class TimerForm(forms.ModelForm):
    class Meta:
        model = Timer
        fields = ['name']

    def __init__(self, *args, **kwargs):
        if 'user' in kwargs:
            self.user = kwargs.pop('user')
        super(TimerForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TimerForm, self).save(commit=False)
        if 'user' in self:
            instance.user = self.user
        instance.save()
        return instance


class TummyTimeForm(forms.ModelForm):
    class Meta:
        model = TummyTime
        fields = ['child', 'start', 'end', 'milestone']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'class': 'datepicker-input',
                'data-toggle': 'datetimepicker',
                'data-target': '#id_end',
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
            timer = Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        instance.save()
        return instance
