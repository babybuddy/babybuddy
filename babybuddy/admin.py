# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from babybuddy import models


class SettingsInline(admin.StackedInline):
    model = models.Settings
    verbose_name = _("Settings")
    verbose_name_plural = _("Settings")
    can_delete = False
    fieldsets = (
        (
            _("Dashboard"),
            {
                "fields": (
                    "dashboard_refresh_rate",
                    "dashboard_hide_empty",
                    "dashboard_hide_age",
                )
            },
        ),
    )


class UserAdmin(BaseUserAdmin):
    inlines = (SettingsInline,)


admin.site.unregister(get_user_model())
admin.site.register(get_user_model(), UserAdmin)
