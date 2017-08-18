# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms

from .models import Child, DiaperChange, Feeding, Sleep, Timer, TummyTime


# Sets the default Child instance if only one exists in the database.
def set_default_child(kwargs):
    instance = kwargs.get('instance', None)
    if instance is None and Child.objects.count() == 1:
        kwargs.update(initial={'child': Child.objects.first()})
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
        super(FeedingForm, self).__init__(*args, **kwargs)


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
        super(SleepForm, self).__init__(*args, **kwargs)


class TimerForm(forms.ModelForm):
    next = forms.CharField(required=False)

    class Meta:
        model = Timer
        fields = ['name']

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
        super(TummyTimeForm, self).__init__(*args, **kwargs)
