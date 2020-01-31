# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf import settings

from core import models


@admin.register(models.Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'birth_date', 'slug')
    list_filter = ('last_name',)
    search_fields = ('first_name', 'last_name', 'birth_date')
    fields = ['first_name', 'last_name', 'birth_date']
    if settings.BABY_BUDDY['ALLOW_UPLOADS']:
        fields.append('picture')


@admin.register(models.DiaperChange)
class DiaperChangeAdmin(admin.ModelAdmin):
    list_display = ('child', 'time', 'wet', 'solid', 'color')
    list_filter = ('child', 'wet', 'solid', 'color')
    search_fields = ('child__first_name', 'child__last_name',)


@admin.register(models.Feeding)
class FeedingAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'child', 'type', 'method',
                    'amount')
    list_filter = ('child', 'type', 'method',)
    search_fields = ('child__first_name', 'child__last_name', 'type',
                     'method',)


@admin.register(models.Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('time', 'child', 'note',)
    list_filter = ('child',)
    search_fields = ('child__last_name',)


@admin.register(models.Sleep)
class SleepAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'child', 'nap')
    list_filter = ('child',)
    search_fields = ('child__first_name', 'child__last_name',)


@admin.register(models.Temperature)
class TemperatureAdmin(admin.ModelAdmin):
    list_display = ('child', 'temperature', 'time',)
    list_filter = ('child',)
    search_fields = ('child__first_name', 'child__last_name', 'temperature',)


@admin.register(models.Timer)
class TimerAdmin(admin.ModelAdmin):
    list_display = ('name', 'child', 'start', 'end', 'duration', 'active',
                    'user')
    list_filter = ('child', 'active', 'user')
    search_fields = ('child__first_name', 'child__last_name', 'name', 'user')


@admin.register(models.TummyTime)
class TummyTimeAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'child', 'milestone',)
    list_filter = ('child',)
    search_fields = ('child__first_name', 'child__last_name', 'milestone',)


@admin.register(models.Weight)
class WeightAdmin(admin.ModelAdmin):
    list_display = ('child', 'weight', 'date',)
    list_filter = ('child',)
    search_fields = ('child__first_name', 'child__last_name', 'weight',)
