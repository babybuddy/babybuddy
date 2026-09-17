# -*- coding: utf-8 -*-
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from core.apps import add_caregiver_group_permissions, add_read_only_group_permissions


class ReadOnlyGroupPermissionsTestCase(TestCase):
    """
    The read-only group is populated by a `post_migrate` receiver. These tests
    run against a freshly migrated database, which is the case the receiver
    previously got wrong: the group was created but left without any
    permissions until a second `migrate` happened to run.
    """

    def test_group_exists(self):
        self.assertTrue(
            Group.objects.filter(
                name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
            ).exists()
        )

    def test_group_has_all_core_view_permissions(self):
        group = Group.objects.get(name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"])
        granted = set(group.permissions.values_list("codename", flat=True))

        expected = {
            f"view_{model}"
            for model in apps.all_models["core"]
            if Permission.objects.filter(codename=f"view_{model}").exists()
        }

        self.assertGreater(len(expected), 0)
        self.assertEqual(expected - granted, set())

    def test_read_only_user_can_view_core_models(self):
        user = get_user_model().objects.create_user(
            username="readonly", password="readonly", is_active=True
        )
        user.groups.add(
            Group.objects.get(name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"])
        )
        # Re-fetch so the permission cache picks up the new group.
        user = get_user_model().objects.get(username="readonly")

        self.assertTrue(user.has_perm("core.view_child"))
        self.assertTrue(user.has_perm("core.view_feeding"))
        self.assertFalse(user.has_perm("core.add_feeding"))


class CaregiverGroupPermissionsTestCase(TestCase):
    expected_codenames = {
        "view_child",
        "view_timer",
        "add_timer",
        "change_timer",
        "view_feeding",
        "add_feeding",
        "change_feeding",
        "view_diaperchange",
        "add_diaperchange",
        "change_diaperchange",
        "view_sleep",
        "add_sleep",
        "change_sleep",
        "view_medication",
        "add_medication",
        "change_medication",
        "view_temperature",
        "add_temperature",
        "change_temperature",
        "view_weight",
        "add_weight",
        "change_weight",
        "view_note",
        "add_note",
        "change_note",
        "view_tummytime",
        "add_tummytime",
        "change_tummytime",
    }

    def setUp(self):
        self.group = Group.objects.get(name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"])

    def test_fresh_group_has_exact_default_permissions(self):
        self.assertEqual(self.group.permissions.count(), 28)
        self.assertEqual(
            set(
                self.group.permissions.values_list(
                    "content_type__app_label", "codename"
                )
            ),
            {("core", codename) for codename in self.expected_codenames},
        )

    def test_foreign_app_codename_collision_is_ignored(self):
        foreign_type = ContentType.objects.create(app_label="foreign", model="child")
        foreign_permission = Permission.objects.create(
            content_type=foreign_type, codename="view_child", name="Can view child"
        )
        core_permission = Permission.objects.get(
            content_type__app_label="core", codename="view_child"
        )
        for sync, group_name in (
            (add_caregiver_group_permissions, "CAREGIVER_GROUP_NAME"),
            (add_read_only_group_permissions, "READ_ONLY_GROUP_NAME"),
        ):
            with self.subTest(group=group_name):
                group = Group.objects.get(name=settings.BABY_BUDDY[group_name])
                group.permissions.clear()
                sync(sender=None)
                self.assertIn(core_permission, group.permissions.all())
                self.assertNotIn(foreign_permission, group.permissions.all())

    def test_sync_is_idempotent(self):
        original_ids = set(self.group.permissions.values_list("pk", flat=True))
        for _ in range(2):
            add_caregiver_group_permissions(sender=None)
        self.assertEqual(
            set(self.group.permissions.values_list("pk", flat=True)), original_ids
        )
        self.assertEqual(self.group.permissions.count(), 28)

    def test_missing_early_permission_is_skipped_until_next_sync(self):
        permission = Permission.objects.get(
            content_type__app_label="core", codename="view_child"
        )
        content_type = permission.content_type
        name = permission.name
        permission.delete()
        self.group.permissions.clear()

        add_caregiver_group_permissions(sender=None)

        self.assertEqual(
            set(self.group.permissions.values_list("codename", flat=True)),
            self.expected_codenames - {"view_child"},
        )
        permission = Permission.objects.create(
            content_type=content_type, codename="view_child", name=name
        )
        add_caregiver_group_permissions(sender=None)
        self.assertIn(permission, self.group.permissions.all())
        self.assertEqual(self.group.permissions.count(), 28)

    def test_sync_restores_defaults_and_retains_manual_permissions(self):
        default = Permission.objects.get(
            content_type__app_label="core", codename="add_feeding"
        )
        extra = Permission.objects.get(
            content_type__app_label="core", codename="delete_feeding"
        )
        self.group.permissions.remove(default)
        self.group.permissions.add(extra)

        add_caregiver_group_permissions(sender=None)

        self.assertEqual(
            set(self.group.permissions.values_list("codename", flat=True)),
            self.expected_codenames | {"delete_feeding"},
        )

    def test_existing_member_receives_sync_updates_after_refetch(self):
        permission = Permission.objects.get(
            content_type__app_label="core", codename="add_feeding"
        )
        self.group.permissions.remove(permission)
        user = get_user_model().objects.create_user(username="caregiver")
        user.groups.add(self.group)
        self.assertFalse(user.has_perm("core.add_feeding"))

        add_caregiver_group_permissions(sender=None)
        user = get_user_model().objects.get(pk=user.pk)

        self.assertTrue(user.has_perm("core.add_feeding"))
        self.assertFalse(user.has_perm("core.delete_feeding"))
