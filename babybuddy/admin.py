# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from babybuddy import models


class SettingsInline(admin.StackedInline):
    model = models.Settings
    verbose_name = _('Settings')
    verbose_name_plural = _('Settings')
    can_delete = False
    fieldsets = (
        (_('Dashboard'), {
            'fields': ('dashboard_refresh_rate',)
        }),
    )


class UserAdmin(BaseUserAdmin):
    inlines = (SettingsInline, )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
