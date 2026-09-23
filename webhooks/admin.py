# -*- coding: utf-8 -*-
from django.contrib import admin

from webhooks import models


@admin.register(models.WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "active", "created", "last_delivery")
    list_filter = ("active",)
    search_fields = ("name", "url")
    readonly_fields = ("created",)


@admin.register(models.WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "type",
        "object_id",
        "endpoint",
        "created",
        "delivered",
        "attempts",
        "next_attempt",
    )
    list_filter = ("type", "endpoint")
    search_fields = ("type", "object_id", "last_error")
    readonly_fields = (
        "endpoint",
        "event_id",
        "type",
        "object_id",
        "created",
        "delivered",
        "attempts",
        "next_attempt",
        "last_error",
    )

    def has_add_permission(self, request):
        # Events come from changes to records. Adding one by hand would be a
        # notification about something that never happened.
        return False
