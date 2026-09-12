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
        # This receiver deliberately has no `sender` filter. `post_migrate` is
        # emitted once per application, in `INSTALLED_APPS` order, and both of
        # the things this receiver depends on are only in place part way
        # through that sequence:
        #
        # - `core`'s permissions are created by `django.contrib.auth`, whose
        #   receiver is connected after this one (`django.contrib.auth` is
        #   listed after `core` in `INSTALLED_APPS`), so on `core`'s own signal
        #   they do not exist yet.
        # - the read-only group itself is created on `babybuddy`'s signal.
        #
        # Restricted to `sender=self` the receiver therefore ran exactly once,
        # too early, and a freshly migrated database ended up with an empty
        # read-only group. Running on every application's signal converges to
        # the complete set instead, and `Permission.objects.add()` makes the
        # repeats idempotent.
        post_migrate.connect(
            add_read_only_group_permissions,
            dispatch_uid="core.add_read_only_group_permissions",
        )
