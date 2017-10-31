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
                'data-target': '#datetimepicker_date',
            }),
        }


class DiaperChangeForm(forms.ModelForm):
    class Meta:
        model = DiaperChange
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

    def clean(self):
        """Additional form validation/cleaning.
        """
        errors = {}

        # One or both of Wet and Solid is required.
        if not self.cleaned_data['wet'] and not self.cleaned_data['solid']:
            errors['wet'] = forms.ValidationError(
                'Wet and/or solid is required.',
                code='missing-wet-or-solid')
            errors['solid'] = forms.ValidationError(
                'Wet and/or solid is required.',
                code='missing-wet-or-solid')

        # Color is required when Solid is selected.
        if self.cleaned_data['solid'] and not self.cleaned_data['color']:
            errors['color'] = forms.ValidationError(
                'Color is required for solid changes.',
                code='missing-color')

        if len(errors) > 0:
            raise forms.ValidationError(errors)

        return self.cleaned_data


class FeedingForm(forms.ModelForm):
    class Meta:
        model = Feeding
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

    def clean(self):
        """Additional form validation/cleaning.
        """
        errors = {}

        # "Formula" Type may only be associated with "Bottle" Method.
        if (self.cleaned_data['type'] == 'formula'
                and self.cleaned_data['method'] != 'bottle'):
            errors['method'] = forms.ValidationError(
                'Only "Bottle" method is allowed with type "Formula".',
                code='bottle-formula-mismatch')

        if len(errors) > 0:
            raise forms.ValidationError(errors)

        return self.cleaned_data

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
            timer = Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        instance.save()
        return instance


class TimerForm(forms.ModelForm):
    class Meta:
        model = Timer
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
        model = TummyTime
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
            timer = Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        instance.save()
        return instance
