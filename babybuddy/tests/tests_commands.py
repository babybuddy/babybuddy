# -*- coding: utf-8 -*-
from django.test import TransactionTestCase
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command

from core.models import Child


class CommandsTestCase(TransactionTestCase):
    def test_migrate(self):
        call_command("migrate", verbosity=0)
        self.assertIsInstance(
            get_user_model().objects.get(username="admin"), get_user_model()
        )

    def test_fake(self):
        call_command("migrate", verbosity=0)
        call_command("fake", children=1, days=7, verbosity=0)
        self.assertEqual(Child.objects.count(), 1)
        call_command("fake", children=2, days=7, verbosity=0)
        self.assertEqual(Child.objects.count(), 3)

    def test_reset(self):
        call_command("reset", verbosity=0, interactive=False)
        self.assertIsInstance(
            get_user_model().objects.get(username="admin"), get_user_model()
        )
        self.assertEqual(Child.objects.count(), 1)

    def test_createuser_staff_caregiver_is_rejected(self):
        call_command("migrate", verbosity=0)
        with self.assertRaisesMessage(
            CommandError, "A user cannot be both staff and caregiver."
        ):
            call_command(
                "createuser",
                "--caregiver",
                "--is-staff",
                username="staffcaregiver",
                password="test",
                verbosity=0,
            )
        self.assertFalse(
            get_user_model().objects.filter(username="staffcaregiver").exists()
        )

    def test_createuser_read_only_staff(self):
        call_command("migrate", verbosity=0)
        call_command(
            "createuser",
            "--read-only",
            "--is-staff",
            username="readonlystaff",
            password="test",
            verbosity=0,
        )
        user = get_user_model().objects.get(username="readonlystaff")
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(
            user.groups.filter(
                name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
            ).exists()
        )
        self.assertFalse(
            user.groups.filter(
                name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"]
            ).exists()
        )

    def test_createuser(self):
        call_command("migrate", verbosity=0)
        call_command(
            "createuser",
            username="regularuser",
            email="regularuser@test.test",
            password="test",
            verbosity=0,
        )
        user = get_user_model().objects.get(username="regularuser")
        self.assertIsInstance(user, get_user_model())
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.email, "regularuser@test.test")

        call_command(
            "createuser",
            "--is-staff",
            username="staffuser",
            email="staffuser@test.test",
            password="test",
            verbosity=0,
        )
        user = get_user_model().objects.get(username="staffuser")
        self.assertIsInstance(user, get_user_model())
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

        call_command(
            "createuser",
            "--read-only",
            username="readonlyuser",
            email="readonlyuser@test.test",
            password="test",
            verbosity=0,
        )
        user = get_user_model().objects.get(username="readonlyuser")
        self.assertIsInstance(user, get_user_model())
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(
            user.groups.filter(
                name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
            ).exists()
        )
        self.assertFalse(
            user.groups.filter(
                name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"]
            ).exists()
        )

        call_command(
            "createuser",
            "--caregiver",
            username="caregiveruser",
            email="caregiveruser@test.test",
            password="test",
            verbosity=0,
        )
        user = get_user_model().objects.get(username="caregiveruser")
        self.assertIsInstance(user, get_user_model())
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(
            user.groups.filter(
                name=settings.BABY_BUDDY["CAREGIVER_GROUP_NAME"]
            ).exists()
        )
        self.assertFalse(
            user.groups.filter(
                name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"]
            ).exists()
        )
        # Caregivers can log the care entries, but nothing administrative.
        self.assertTrue(user.has_perm("core.add_feeding"))
        self.assertTrue(user.has_perm("core.add_diaperchange"))
        self.assertTrue(user.has_perm("core.add_sleep"))
        self.assertTrue(user.has_perm("core.add_timer"))
        self.assertTrue(user.has_perm("core.add_medication"))
        self.assertTrue(user.has_perm("core.add_temperature"))
        self.assertTrue(user.has_perm("core.add_weight"))
        self.assertTrue(user.has_perm("core.add_note"))
        self.assertTrue(user.has_perm("core.add_tummytime"))
        self.assertFalse(user.has_perm("core.add_pumping"))
        self.assertFalse(user.has_perm("core.add_height"))
        self.assertFalse(user.has_perm("core.add_bmi"))
        self.assertFalse(user.has_perm("core.add_headcircumference"))
        self.assertFalse(user.has_perm("core.add_tag"))
        self.assertFalse(user.has_perm("core.delete_feeding"))

        with self.assertRaises(CommandError):
            call_command(
                "createuser",
                "--read-only",
                "--caregiver",
                username="bothuser",
                email="both@test.test",
                password="test",
                verbosity=0,
            )
