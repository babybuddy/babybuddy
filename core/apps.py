# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

# Models a caregiver may see. `view` is granted for all of them so the child
# dashboard and the recent-entry lists render; `add`/`change` only for the
# entry types a caregiver is expected to log.
CAREGIVER_VIEW_MODELS = (
    "child",
    "timer",
    "feeding",
    "diaperchange",
    "sleep",
)

CAREGIVER_ADD_CHANGE_MODELS = (
    "timer",
    "feeding",
    "diaperchange",
    "sleep",
)


def _permissions(codenames):
    from django.contrib.auth.models import Permission

    permissions = []
    for codename in codenames:
        try:
            permissions.append(Permission.objects.get(codename=codename))
        except Permission.DoesNotExist:
            continue
    return permissions


def _add_group_permissions(group_name, permissions):
    from django.contrib.auth.models import Group

    if not permissions:
        return
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        return
    group.permissions.add(*permissions)


def add_read_only_group_permissions(sender, **kwargs):
    from django.apps import apps

    _add_group_permissions(
        settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"],
        _permissions(f"view_{model}" for model in apps.all_models["core"]),
    )


def add_caregiver_group_permissions(sender, **kwargs):
    codenames = [f"view_{model}" for model in CAREGIVER_VIEW_MODELS]
    for model in CAREGIVER_ADD_CHANGE_MODELS:
        codenames += [f"add_{model}", f"change_{model}"]

    _add_group_permissions(
        settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"], _permissions(codenames)
    )


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        post_migrate.connect(add_read_only_group_permissions, sender=self)
        # The caregiver receiver deliberately has no `sender` filter:
        # `post_migrate` is emitted once per application, in `INSTALLED_APPS`
        # order, and `core`'s permissions are created by
        # `django.contrib.auth`, which is listed after `core`. Restricted to
        # `sender=self` it would run too early, before the permissions exist.
        post_migrate.connect(
            add_caregiver_group_permissions,
            dispatch_uid="core.add_caregiver_group_permissions",
        )
