# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _

from core import models


def set_initial_values(kwargs, form_type):
    """
    Sets initial value for add forms based on provided kwargs.

    :param kwargs: Keyword arguments.
    :param form_type: Class of the type of form being initialized.
    :return: Keyword arguments with updated "initial" values.
    """

    # Never update initial values for existing instance (e.g. edit operation).
    if kwargs.get('instance', None):
        return kwargs

    # Add the "initial" kwarg if it does not already exist.
    if not kwargs.get('initial'):
        kwargs.update(initial={})

    # Set Child based on `child` kwarg or single Chile database.
    child_slug = kwargs.get('child', None)
    if child_slug:
        kwargs['initial'].update({
            'child': models.Child.objects.filter(slug=child_slug).first(),
        })
    elif models.Child.count() == 1:
        kwargs['initial'].update({'child': models.Child.objects.first()})

    # Set start and end time based on Timer from `timer` kwarg.
    timer_id = kwargs.get('timer', None)
    if timer_id:
        timer = models.Timer.objects.get(id=timer_id)
        kwargs['initial'].update({
            'timer': timer,
            'start': timer.start,
            'end': timer.end or timezone.now()
        })

    # Set type and method values for Feeding instance based on last feed.
    if form_type == FeedingForm and 'child' in kwargs['initial']:
        last_feeding = models.Feeding.objects.filter(
            child=kwargs['initial']['child']).order_by('end').last()
        if last_feeding:
            last_type = last_feeding.type
            last_feed_args = {'type': last_feeding.type}
            if last_type in ['formula', 'fortified breast milk']:
                last_feed_args['method'] = 'bottle'
            kwargs['initial'].update(last_feed_args)

    # Remove custom kwargs so they do not interfere with `super` calls.
    for key in ['child', 'timer']:
        try:
            kwargs.pop(key)
        except KeyError:
            pass

    return kwargs


class CoreModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Set `timer_id` so the Timer can be stopped in the `save` method.
        self.timer_id = kwargs.get('timer', None)
        kwargs = set_initial_values(kwargs, type(self))
        super(CoreModelForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        # If `timer_id` is present, stop the Timer.
        instance = super(CoreModelForm, self).save(commit=False)
        if self.timer_id:
            timer = models.Timer.objects.get(id=self.timer_id)
            timer.stop(instance.end)
        if commit:
            instance.save()
        return instance


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
                'readonly': 'readonly',
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
                _('Name does not match child name.'), code='confirm_mismatch')
        return confirm_name

    def save(self, commit=True):
        instance = self.instance
        self.instance.delete()
        return instance


class DiaperChangeForm(CoreModelForm):
    class Meta:
        model = models.DiaperChange
        fields = ['child', 'time', 'wet', 'solid', 'color', 'amount', 'notes']
        widgets = {
            'time': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_time',
            }),
            'notes': forms.Textarea(attrs={'rows': 5}),
        }


class FeedingForm(CoreModelForm):
    class Meta:
        model = models.Feeding
        fields = ['child', 'start', 'end', 'type', 'method', 'amount', 'notes']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_end',
            }),
            'notes': forms.Textarea(attrs={'rows': 5}),
        }


class NoteForm(CoreModelForm):
    class Meta:
        model = models.Note
        fields = ['child', 'note', 'time']
        widgets = {
            'time': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_time',
            }),
        }


class SleepForm(CoreModelForm):
    class Meta:
        model = models.Sleep
        fields = ['child', 'start', 'end', 'notes']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_end',
            }),
            'notes': forms.Textarea(attrs={'rows': 5}),
        }


class TemperatureForm(CoreModelForm):
    class Meta:
        model = models.Temperature
        fields = ['child', 'temperature', 'time', 'notes']
        widgets = {
            'time': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_time',
            }),
            'notes': forms.Textarea(attrs={'rows': 5}),
        }


class TimerForm(CoreModelForm):
    class Meta:
        model = models.Timer
        fields = ['child', 'name', 'start']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
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


class TummyTimeForm(CoreModelForm):
    class Meta:
        model = models.TummyTime
        fields = ['child', 'start', 'end', 'milestone']
        widgets = {
            'start': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_start',
            }),
            'end': forms.DateTimeInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_end',
            }),
        }


class WeightForm(CoreModelForm):
    class Meta:
        model = models.Weight
        fields = ['child', 'weight', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'readonly': 'readonly',
                'data-target': '#datetimepicker_date',
            }),
            'notes': forms.Textarea(attrs={'rows': 5}),
        }
