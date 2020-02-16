# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf import settings

from import_export import resources
from import_export.admin import ImportExportMixin

from core import models


class ChildImportExportResource(resources.ModelResource):
    class Meta:
        model = models.Child
        exclude = ('picture', 'slug')


@admin.register(models.Child)
class ChildAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'birth_date', 'slug')
    list_filter = ('last_name',)
    search_fields = ('first_name', 'last_name', 'birth_date')
    fields = ['first_name', 'last_name', 'birth_date']
    if settings.BABY_BUDDY['ALLOW_UPLOADS']:
        fields.append('picture')
    resource_class = ChildImportExportResource


class DiaperChangeImportExportResource(resources.ModelResource):
    class Meta:
        model = models.DiaperChange


@admin.register(models.DiaperChange)
class DiaperChangeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('child', 'time', 'wet', 'solid', 'color')
    list_filter = ('child', 'wet', 'solid', 'color')
    search_fields = ('child__first_name', 'child__last_name',)
    resource_class = DiaperChangeImportExportResource


class FeedingImportExportResource(resources.ModelResource):
    class Meta:
        model = models.Feeding


@admin.register(models.Feeding)
class FeedingAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'child', 'type', 'method',
                    'amount')
    list_filter = ('child', 'type', 'method',)
    search_fields = ('child__first_name', 'child__last_name', 'type',
                     'method',)
    resource_class = FeedingImportExportResource


class NoteImportExportResource(resources.ModelResource):
    class Meta:
        model = models.Note


@admin.register(models.Note)
class NoteAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('time', 'child', 'note',)
    list_filter = ('child',)
    search_fields = ('child__last_name',)
    resource_class = NoteImportExportResource


class SleepImportExportResource(resources.ModelResource):
    class Meta:
        model = models.Sleep
        exclude = ('duration',)


@admin.register(models.Sleep)
class SleepAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'child', 'nap')
    list_filter = ('child',)
    search_fields = ('child__first_name', 'child__last_name',)
    resource_class = SleepImportExportResource


class TemperatureImportExportResource(resources.ModelResource):
    class Meta:
        model = models.Temperature


@admin.register(models.Temperature)
class TemperatureAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('child', 'temperature', 'time',)
    list_filter = ('child',)
    search_fields = ('child__first_name', 'child__last_name', 'temperature',)
    resource_class = TemperatureImportExportResource


@admin.register(models.Timer)
class TimerAdmin(admin.ModelAdmin):
    list_display = ('name', 'child', 'start', 'end', 'duration', 'active',
                    'user')
    list_filter = ('child', 'active', 'user')
    search_fields = ('child__first_name', 'child__last_name', 'name', 'user')


class TummyTimeImportExportResource(resources.ModelResource):
    class Meta:
        model = models.TummyTime


@admin.register(models.TummyTime)
class TummyTimeAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('start', 'end', 'duration', 'child', 'milestone',)
    list_filter = ('child',)
    search_fields = ('child__first_name', 'child__last_name', 'milestone',)
    resource_class = TummyTimeImportExportResource


class WeightImportExportResource(resources.ModelResource):
    class Meta:
        model = models.Weight


@admin.register(models.Weight)
class WeightAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ('child', 'weight', 'date',)
    list_filter = ('child',)
    search_fields = ('child__first_name', 'child__last_name', 'weight',)
    resource_class = WeightImportExportResource
