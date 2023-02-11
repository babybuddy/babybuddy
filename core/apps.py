# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate


def add_read_only_group_permissions(sender, **kwargs):
    from django.apps import apps
    from django.contrib.auth.models import Group, Permission

    permissions = []
    for model in apps.all_models["core"]:
        try:
            permissions.append(Permission.objects.get(codename=f"view_{model}"))
        except Permission.DoesNotExist:
            continue

    if len(permissions) > 0:
        try:
            group = Group.objects.get(name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"])
            group.permissions.add(*permissions)
        except Group.DoesNotExist:
            pass


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        post_migrate.connect(add_read_only_group_permissions, sender=self)
