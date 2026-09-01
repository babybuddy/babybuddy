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

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_staff",
            "is_read_only",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs["instance"]
        if user:
            kwargs["initial"].update(
                {
                    "is_read_only": user.groups.filter(
                        name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
                    ).exists()
                }
            )
        super(BabyBuddyUserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super(BabyBuddyUserForm, self).save(commit=False)
        is_read_only = self.cleaned_data["is_read_only"]
        if is_read_only:
            user.is_superuser = False
        else:
            user.is_superuser = True
        if commit:
            user.save()
        readonly_group = Group.objects.get(
            name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
        )
        if is_read_only:
            user.groups.add(readonly_group.id)
        else:
            user.groups.remove(readonly_group.id)
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
    dashboard_cards = forms.MultipleChoiceField(
        label=_("Dashboard cards"),
        help_text=_("Cards to show on child dashboards."),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )

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

    def __init__(self, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)
        # Imported here to avoid a circular import at module load time.
        from dashboard.cards import get_card_choices

        self.fields["dashboard_cards"].choices = get_card_choices()
        hidden = set(self.instance.dashboard_hidden_cards or [])
        self.initial["dashboard_cards"] = [
            card_id
            for card_id, _label in self.fields["dashboard_cards"].choices
            if card_id not in hidden
        ]

    def save(self, commit=True):
        instance = super(UserSettingsForm, self).save(commit=False)
        # Visible cards are stored as their complement so that newly added
        # cards (and activity types) are shown by default.
        visible = set(self.cleaned_data.get("dashboard_cards") or [])
        instance.dashboard_hidden_cards = [
            card_id
            for card_id, _label in self.fields["dashboard_cards"].choices
            if card_id not in visible
        ]
        if commit:
            instance.save()
        return instance
