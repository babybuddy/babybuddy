# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms

from .models import Child, DiaperChange, Feeding, Sleep, Timer, TummyTime


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


class TimerForm(forms.ModelForm):
    next = forms.CharField(required=False)

    class Meta:
        model = Timer
        fields = ['name']


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
