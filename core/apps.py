# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.conf import settings
from django.db.models.signals import post_migrate

# Models a caregiver may see. `view` is granted for all of them so the child
# dashboard and the recent-entry lists render; `add`/`change` only for the
# entry types a caregiver is expected to log.
#
# A caregiver is deliberately given most of the care-entry types: someone
# looking after a child needs to record what happened, and the model is rigid
# (a permission is instance-wide and the group is the only role), so the safer
# default is more access rather than less. What stays out is what a caregiver
# has no reason to record: pumping, the growth measurements that are tracked
# over months (height, BMI, head circumference), and everything administrative
# — children, users, tags and site settings. `delete` is never granted.
CAREGIVER_VIEW_MODELS = (
    "child",
    "timer",
    "feeding",
    "diaperchange",
    "sleep",
    "medication",
    "temperature",
    "weight",
    "note",
    "tummytime",
)

CAREGIVER_ADD_CHANGE_MODELS = (
    "timer",
    "feeding",
    "diaperchange",
    "sleep",
    "medication",
    "temperature",
    "weight",
    "note",
    "tummytime",
)


def _permissions(codenames):
    from django.contrib.auth.models import Permission

    permissions = []
    for codename in codenames:
        try:
            permissions.append(
                Permission.objects.get(
                    content_type__app_label="core", codename=codename
                )
            )
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
        # The read only group receiver deliberately has no `sender` filter.
        # `post_migrate` is emitted once per application, in `INSTALLED_APPS`
        # order, and both of the things this receiver depends on are only in
        # place part way through that sequence:
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
        # The caregiver receiver deliberately has no `sender` filter:
        # `post_migrate` is emitted once per application, in `INSTALLED_APPS`
        # order, and `core`'s permissions are created by
        # `django.contrib.auth`, which is listed after `core`. Restricted to
        # `sender=self` it would run too early, before the permissions exist.
        post_migrate.connect(
            add_caregiver_group_permissions,
            dispatch_uid="core.add_caregiver_group_permissions",
        )
