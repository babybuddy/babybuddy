# -*- coding: utf-8 -*-
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from .models import Settings


class BabyBuddyUserForm(forms.ModelForm):
    is_read_only = forms.BooleanField(
        required=False,
        label=_("Read only"),
        help_text=_("Restricts user to viewing data only."),
    )
    is_caregiver = forms.BooleanField(
        required=False,
        label=_("Caregiver"),
        help_text=_(
            "Allows adding and editing care entries (feedings, diaper changes, "
            "sleep, timers, medication, temperature, weight, notes and tummy "
            "time) for every child. Cannot delete entries or reach pumping, "
            "height, BMI, head circumference, user management or settings."
        ),
    )

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_read_only",
            "is_caregiver",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs["instance"]
        if user:
            kwargs["initial"].update(
                {
                    "is_read_only": user.groups.filter(
                        name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
                    ).exists(),
                    "is_caregiver": user.groups.filter(
                        name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"]
                    ).exists(),
                }
            )
        super(BabyBuddyUserForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("is_read_only") and cleaned_data.get("is_caregiver"):
            self.add_error(
                "is_caregiver",
                _("A user cannot be both read only and caregiver."),
            )
        if cleaned_data.get("is_staff") and cleaned_data.get("is_caregiver"):
            self.add_error(
                "is_caregiver",
                _("A user cannot be both staff and caregiver."),
            )
        return cleaned_data

    def save(self, commit=True):
        user = super(BabyBuddyUserForm, self).save(commit=False)
        is_read_only = self.cleaned_data["is_read_only"]
        is_caregiver = self.cleaned_data.get("is_caregiver", False)
        if is_read_only or is_caregiver:
            user.is_superuser = False
        else:
            user.is_superuser = True
        if commit:
            user.save()
        readonly_group = Group.objects.get(
            name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
        )
        caregiver_group = Group.objects.get(
            name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"]
        )
        if is_read_only:
            user.groups.add(readonly_group.id)
        else:
            user.groups.remove(readonly_group.id)
        if is_caregiver:
            user.groups.add(caregiver_group.id)
        else:
            user.groups.remove(caregiver_group.id)
        return user


class UserAddForm(BabyBuddyUserForm, UserCreationForm):
    pass


class UserUpdateForm(BabyBuddyUserForm):
    pass


class UserForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]


class UserPasswordForm(PasswordChangeForm):
    class Meta:
        fields = ["old_password", "new_password1", "new_password2"]


class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = Settings
        fields = [
            "dashboard_refresh_rate",
            "dashboard_hide_empty",
            "dashboard_hide_age",
            "language",
            "timezone",
            "pagination_count",
        ]
