# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from .models import Child, DiaperChange, Feeding, Note, Sleep, TummyTime


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'birth_date',)
    list_filter = ('last_name',)
    search_fields = ('first_name', 'last_name', 'birth_date',)


@admin.register(DiaperChange)
class DiaperChangeAdmin(admin.ModelAdmin):
    list_display = ('baby', 'time', 'wet', 'solid', 'color')
    list_filter = ('baby', 'wet', 'solid', 'color')
    search_fields = ('baby__first_name', 'baby__last_name',)


@admin.register(Feeding)
class FeedingAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'baby', 'type', 'method',)
    list_filter = ('baby', 'type', 'method',)
    search_fields = ('baby__first_name', 'baby__last_name', 'type', 'method',)


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('time', 'baby', 'note',)
    list_filter = ('baby',)
    search_fields = ('baby__last_name',)


@admin.register(Sleep)
class SleepAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'baby',)
    list_filter = ('baby',)
    search_fields = ('baby__first_name', 'baby__last_name',)


@admin.register(TummyTime)
class TummyTimeAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'baby', 'milestone',)
    list_filter = ('baby',)
    search_fields = ('baby__first_name', 'baby__last_name', 'milestone',)
