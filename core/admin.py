# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf import settings

from import_export import fields, resources
from import_export.admin import ImportExportMixin, ExportActionMixin

from core import models


class ImportExportResourceBase(resources.ModelResource):
    id = fields.Field(attribute="id")
    child = fields.Field(attribute="child_id", column_name="child_id")
    child_first_name = fields.Field(attribute="child__first_name", readonly=True)
    child_last_name = fields.Field(attribute="child__last_name", readonly=True)

    class Meta:
        clean_model_instances = True
        exclude = ("duration",)
        export_order = ("id", "child_id", "child_first_name", "child_last_name")


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
    list_display = ("first_name", "last_name", "birth_date", "birth_time", "slug")
    list_filter = ("last_name",)
    search_fields = ("first_name", "last_name", "birth_date")
    fields = ["first_name", "last_name", "birth_date", "birth_time"]
    if settings.BABY_BUDDY["ALLOW_UPLOADS"]:
        fields.append("picture")
    resource_class = ChildImportExportResource


class PumpingImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Pumping


@admin.register(models.Pumping)
class PumpingAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "start",
        "end",
        "duration",
        "child",
        "amount",
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


class FeedingOptionResource(ImportExportResourceBase):
    class Meta:
        model = models.FeedingOption


@admin.register(models.FeedingOption)
class FeedingOptionAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("field_type", "value", "parent")
    list_filter = ("field_type",)
    search_fields = ("value",)
    resource_class = FeedingOptionResource


class FeedingImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Feeding


@admin.register(models.Feeding)
class FeedingAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "start",
        "end",
        "duration",
        "child",
        "type",
        "method",
        "amount",
        "feed_inventory",
    )
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


class MedicationImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Medication


@admin.register(models.Medication)
class MedicationAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "time",
        "child",
        "name",
        "dosage",
        "dosage_unit",
    )
    list_filter = ("child", "dosage_unit", "tags")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "name",
    )
    resource_class = MedicationImportExportResource


class PrescriptionImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Prescription


@admin.register(models.Prescription)
class PrescriptionAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        "medication_name",
        "child",
        "dosage",
        "dosage_unit",
        "frequency",
        "active",
        "start_date",
        "end_date",
    )
    list_filter = ("active", "dosage_unit", "child")
    search_fields = ("medication_name", "prescribing_doctor", "notes")
    date_hierarchy = "start_date"
    resource_class = PrescriptionImportExportResource


class NoteImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.Note
        exclude = ("image",)


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


class TagImportExportResource(resources.ModelResource):
    id = fields.Field(attribute="id")

    class Meta:
        model = models.Tag
        exclude = ("slug", "last_used")


@admin.register(models.Tag)
class TagAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("name", "slug", "color", "last_used")
    ordering = ("name", "slug")
    search_fields = ("name", "color")
    prepopulated_fields = {"slug": ["name"]}
    resource_class = TagImportExportResource


@admin.register(models.ProductLine)
class ProductLineAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("item_type", "brand", "line")
    list_filter = ("item_type",)
    search_fields = ("brand", "line")


@admin.register(models.SupplyItem)
class SupplyItemAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("child", "product_line", "size", "quantity", "purchase_date")
    list_filter = ("product_line__item_type", "product_line__brand", "size")
    search_fields = ("product_line__brand", "product_line__line", "size", "notes")
    raw_id_fields = ("product_line",)


@admin.register(models.SpitUp)
class SpitUpAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("child", "time", "amount", "appearance", "related_feeding")
    list_filter = ("amount", "appearance")
    search_fields = ("appearance", "notes")
    raw_id_fields = ("related_feeding",)


@admin.register(models.EquipmentItem)
class EquipmentItemAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("child", "product_line", "size", "quantity", "acquired_date", "source", "disposal_status")
    list_filter = ("product_line__item_type", "disposal_status")
    search_fields = ("source", "notes")
    raw_id_fields = ("product_line",)


class FeedInventoryImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.FeedInventory


@admin.register(models.FeedInventory)
class FeedInventoryAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("type", "amount", "amount_unit", "storage_location", "status", "expressed_at", "child")
    list_filter = ("type", "storage_location", "status", "child")
    search_fields = (
        "child__first_name",
        "child__last_name",
        "notes",
        "amount",
    )
    resource_class = FeedInventoryImportExportResource


@admin.register(models.DoctorVisit)
class DoctorVisitAdmin(admin.ModelAdmin):
    list_display = ("child", "date_time", "appointment_type", "doctor_name", "practice")
    list_filter = ("appointment_type",)
    search_fields = ("doctor_name", "reason", "diagnosis")
@admin.register(models.InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ("supply_item", "delta", "transaction_type", "quantity_after", "created_at")
    list_filter = ("transaction_type",)
    search_fields = ("note",)
    ordering = ("-created_at",)
    readonly_fields = ("supply_item", "delta", "transaction_type", "source_id", "quantity_after", "note", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(models.InventoryAdjustment)
class InventoryAdjustmentAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("supply_item", "count_time", "physical_count", "adjustment_type", "reason")
    list_filter = ("adjustment_type",)
    search_fields = ("reason",)
    ordering = ("-count_time",)


class FormulaStockImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.FormulaStock


@admin.register(models.FormulaStock)
class FormulaStockAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("product_line", "form", "container_size", "quantity", "opened_at", "expiry_date", "is_reserve")
    list_filter = ("form", "is_reserve")
    search_fields = ("product_line__brand", "product_line__line", "notes")
    resource_class = FormulaStockImportExportResource


class PreparedFeedImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.PreparedFeed


@admin.register(models.PreparedFeed)
class PreparedFeedAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("prepared_from", "amount", "amount_remaining", "prepared_at", "status")
    list_filter = ("prepared_from", "status")
    search_fields = ("notes",)
    resource_class = PreparedFeedImportExportResource


class FormulaStockEventImportExportResource(ImportExportResourceBase):
    class Meta:
        model = models.FormulaStockEvent


@admin.register(models.FormulaStockEvent)
class FormulaStockEventAdmin(ImportExportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("type", "stock", "prepared_feed", "delta_grams", "delta_ml", "created_at")
    list_filter = ("type",)
    search_fields = ("note",)
    ordering = ("-created_at",)
    resource_class = FormulaStockEventImportExportResource

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

