# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from babybuddy import models


class SettingsInline(admin.StackedInline):
    model = models.Settings
    verbose_name_plural = 'Settings'
    can_delete = False
    fieldsets = (
        ('Dashboard', {
            'fields': ('dashboard_refresh_rate',)
        }),
    )


class UserAdmin(BaseUserAdmin):
    inlines = (SettingsInline, )


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
