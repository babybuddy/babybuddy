# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf import settings

from import_export import fields, resources
from import_export.admin import ImportExportMixin, ExportActionMixin

from core import models
from core.forms import TagAdminForm


class ImportExportResourceBase(resources.ModelResource):
    id = fields.Field(attribute="id")
    child = fields.Field(attribute="child_id", column_name="child_id")
    child_first_name = fields.Field(attribute="child__first_name", readonly=True)
    child_last_name = fields.Field(attribute="child__last_name", readonly=True)

    class Meta:
        clean_model_instances = True
        exclude = ("duration",)


class BMIImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.BMI


@admin.register(models.BMI)
class BMIAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "bmi",
        "date",
    )
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "bmi",
    )
    resource_class = BMIImportExportResource


class ChildImportExportResource(resources.ModelResource):
    class Meta:
        model = models.Child
        exclude = ("picture", "slug")


@admin.register(models.Child)
class ChildAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("first_name", "last_name", "birth_date", "slug")
    list_filter = ("last_name",)
    search_fields = ("first_name", "last_name", "birth_date")
    fields = ["first_name", "last_name", "birth_date"]
    if settings.BABY_BUDDY["ALLOW_UPLOADS"]:
        fields.append("picture")
    resource_class = ChildImportExportResource


class PumpingImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Pumping


@admin.register(models.Pumping)
class PumpingAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "amount",
        "time",
    )
    list_filter = ("child",)
    search_fields = (
        "child__first_name",
        "child__last_name",
        "amount",
    )
    resource_class = PumpingImportExportResource


class DiaperChangeImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.DiaperChange


@admin.register(models.DiaperChange)
class DiaperChangeAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("child", "time", "wet", "solid", "color")
    list_filter = ("child", "wet", "solid", "color", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
    )
    resource_class = DiaperChangeImportExportResource


class FeedingImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Feeding


@admin.register(models.Feeding)
class FeedingAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("start", "end", "duration", "child", "type", "method", "amount")
    list_filter = (
        "child",
        "type",
        "method",
        "tags",
    )
    search_fields = (
        "child__first_name",
        "child__last_name",
        "type",
        "method",
    )
    resource_class = FeedingImportExportResource


class HeadCircumferenceImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.HeadCircumference


@admin.register(models.HeadCircumference)
class HeadCircumferenceAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "head_circumference",
        "date",
    )
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "head_circumference",
    )
    resource_class = HeadCircumferenceImportExportResource


class HeightImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Height


@admin.register(models.Height)
class HeightAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "height",
        "date",
    )
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "height",
    )
    resource_class = HeightImportExportResource


class NoteImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Note


@admin.register(models.Note)
class NoteAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "time",
        "child",
        "note",
    )
    list_filter = ("child", "tags")
    search_fields = ("child__last_name",)
    resource_class = NoteImportExportResource


class SleepImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Sleep


@admin.register(models.Sleep)
class SleepAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("start", "end", "duration", "child", "nap")
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
    )
    resource_class = SleepImportExportResource


class TemperatureImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Temperature


@admin.register(models.Temperature)
class TemperatureAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "temperature",
        "time",
    )
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "temperature",
    )
    resource_class = TemperatureImportExportResource


@admin.register(models.Timer)
class TimerAdmin(admin.ModelAdmin):
    list_display = ("name", "child", "start", "duration", "user")
    list_filter = ("child", "user")
    search_fields = ("child__first_name", "child__last_name", "name", "user")


class TummyTimeImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.TummyTime


@admin.register(models.TummyTime)
class TummyTimeAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "start",
        "end",
        "duration",
        "child",
        "milestone",
    )
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "milestone",
    )
    resource_class = TummyTimeImportExportResource


class WeightImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Weight


@admin.register(models.Weight)
class WeightAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "child",
        "weight",
        "date",
    )
    list_filter = ("child", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "weight",
    )
    resource_class = WeightImportExportResource


class TaggedItemInline(admin.StackedInline):
    model = models.Tagged


class TagImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Tag


@admin.register(models.Tag)
class TagAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    form = TagAdminForm
    inlines = [TaggedItemInline]
    list_display = ["name", "slug", "color", "last_used"]
    ordering = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ["name"]}
    resource_class = TagImportExportResource
