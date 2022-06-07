# -*- coding: utf-8 -*-
from django import forms
from django.forms import widgets
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext as _

from taggit.forms import TagField

from core import models
from core.widgets import TagsEditor


def set_initial_values(kwargs, form_type):
    """
    Sets initial value for add forms based on provided kwargs.

    :param kwargs: Keyword arguments.
    :param form_type: Class of the type of form being initialized.
    :return: Keyword arguments with updated "initial" values.
    """

    # Never update initial values for existing instance (e.g. edit operation).
    if kwargs.get("instance", None):
        return kwargs

    # Add the "initial" kwarg if it does not already exist.
    if not kwargs.get("initial"):
        kwargs.update(initial={})

    # Set Child based on `child` kwarg or single Chile database.
    child_slug = kwargs.get("child", None)
    if child_slug:
        kwargs["initial"].update(
            {
                "child": models.Child.objects.filter(slug=child_slug).first(),
            }
        )
    elif models.Child.count() == 1:
        kwargs["initial"].update({"child": models.Child.objects.first()})

    # Set start and end time based on Timer from `timer` kwarg.
    timer_id = kwargs.get("timer", None)
    if timer_id:
        timer = models.Timer.objects.get(id=timer_id)
        kwargs["initial"].update(
            {"timer": timer, "start": timer.start, "end": timer.end or timezone.now()}
        )

    # Set type and method values for Feeding instance based on last feed.
    if form_type == FeedingForm and "child" in kwargs["initial"]:
        last_feeding = (
            models.Feeding.objects.filter(child=kwargs["initial"]["child"])
            .order_by("end")
            .last()
        )
        if last_feeding:
            last_method = last_feeding.method
            last_feed_args = {"type": last_feeding.type}
            if last_method not in ["left breast", "right breast"]:
                last_feed_args["method"] = last_method
            kwargs["initial"].update(last_feed_args)

    # Remove custom kwargs so they do not interfere with `super` calls.
    for key in ["child", "timer"]:
        try:
            kwargs.pop(key)
        except KeyError:
            pass

    return kwargs


class CoreModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Set `timer_id` so the Timer can be stopped in the `save` method.
        self.timer_id = kwargs.get("timer", None)
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
            self.save_m2m()
        return instance


class ChildForm(forms.ModelForm):
    class Meta:
        model = models.Child
        fields = ["first_name", "last_name", "birth_date"]
        if settings.BABY_BUDDY["ALLOW_UPLOADS"]:
            fields.append("picture")
        widgets = {
            "birth_date": forms.DateInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_date",
                }
            ),
        }


class ChildDeleteForm(forms.ModelForm):
    confirm_name = forms.CharField(max_length=511)

    class Meta:
        model = models.Child
        fields = []

    def clean_confirm_name(self):
        confirm_name = self.cleaned_data["confirm_name"]
        if confirm_name != str(self.instance):
            raise forms.ValidationError(
                _("Name does not match child name."), code="confirm_mismatch"
            )
        return confirm_name

    def save(self, commit=True):
        instance = self.instance
        self.instance.delete()
        return instance


class TaggableModelForm(forms.ModelForm):
    tags = TagField(
        widget=TagsEditor,
        required=False,
        strip=True,
        help_text=_(
            "Click on the tags to add (+) or remove (-) tags or use the text editor to create new tags."
        ),
    )


class PumpingForm(CoreModelForm):
    class Meta:
        model = models.Pumping
        fields = ["child", "amount", "time", "notes"]
        widgets = {
            "time": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_time",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class DiaperChangeForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.DiaperChange
        fields = ["child", "time", "wet", "solid", "color", "amount", "notes", "tags"]
        widgets = {
            "time": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_time",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class FeedingForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.Feeding
        fields = ["child", "start", "end", "type", "method", "amount", "notes", "tags"]
        widgets = {
            "start": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_start",
                }
            ),
            "end": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_end",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class NoteForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.Note
        fields = ["child", "note", "time", "tags"]
        widgets = {
            "time": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_time",
                }
            )
        }


class SleepForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.Sleep
        fields = ["child", "start", "end", "notes", "tags"]
        widgets = {
            "start": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_start",
                }
            ),
            "end": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_end",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class TemperatureForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.Temperature
        fields = ["child", "temperature", "time", "notes", "tags"]
        widgets = {
            "time": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_time",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class TimerForm(CoreModelForm):
    class Meta:
        model = models.Timer
        fields = ["child", "name", "start"]
        widgets = {
            "start": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_start",
                }
            )
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(TimerForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TimerForm, self).save(commit=False)
        instance.user = self.user
        instance.save()
        return instance


class TummyTimeForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.TummyTime
        fields = ["child", "start", "end", "milestone", "tags"]
        widgets = {
            "start": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_start",
                }
            ),
            "end": forms.DateTimeInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_end",
                }
            ),
        }


class WeightForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.Weight
        fields = ["child", "weight", "date", "notes", "tags"]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_date",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class HeightForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.Height
        fields = ["child", "height", "date", "notes", "tags"]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_date",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class HeadCircumferenceForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.HeadCircumference
        fields = ["child", "head_circumference", "date", "notes", "tags"]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_date",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class BMIForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.BMI
        fields = ["child", "bmi", "date", "notes", "tags"]
        widgets = {
            "date": forms.DateInput(
                attrs={
                    "autocomplete": "off",
                    "data-td-target": "#datetimepicker_date",
                }
            ),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class TagAdminForm(forms.ModelForm):
    class Meta:
        widgets = {"color": widgets.TextInput(attrs={"type": "color"})}
