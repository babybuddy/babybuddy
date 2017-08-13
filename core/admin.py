# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Baby, Feeding, Sleep


@admin.register(Baby)
class BabyAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'birth_date',)
    search_fields = ('first_name', 'last_name', 'birth_date',)


@admin.register(Feeding)
class FeedingAdmin(admin.ModelAdmin):
    list_display = ('baby', 'start', 'end', 'duration', 'type', 'method',)
    search_fields = ('baby__first_name', 'baby__last_name', 'type', 'method')


@admin.register(Sleep)
class SleepAdmin(admin.ModelAdmin):
    list_display = ('baby', 'start', 'end', 'duration',)
    search_fields = ('baby__first_name', 'baby__last_name',)
