# -*- coding: utf-8 -*-
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase


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
