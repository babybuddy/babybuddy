# -*- coding: utf-8 -*-
import os
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from core.models import Child
from babybuddy.templatetags import babybuddy


class DevBuildBannerTestCase(TestCase):
    def test_banner_empty_when_env_unset(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BB_BUILD_TAG", None)
            os.environ.pop("BB_BUILD_TIME", None)
            self.assertEqual(babybuddy.dev_build_banner(), "")

    def test_banner_tag_only(self):
        # clear=False leaks the deployed container's real BB_BUILD_TIME
        # env into this test (issue #51) — pop it so the tag-only branch
        # is isolated.
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BB_BUILD_TIME", None)
            with mock.patch.dict(os.environ, {"BB_BUILD_TAG": "bb-20260820.4"}):
                self.assertEqual(babybuddy.dev_build_banner(), "bb-20260820.4")

    def test_banner_tag_and_time_localized(self):
        # 17:53 UTC == 13:53 America/New_York (EDT). The banner must
        # show the user's wall clock, never the baked UTC string.
        timezone.activate("America/New_York")
        try:
            with mock.patch.dict(os.environ, {
                "BB_BUILD_TAG": "bb-20260820.4",
                "BB_BUILD_TIME": "2026-08-20 17:53 UTC",
            }):
                self.assertEqual(
                    babybuddy.dev_build_banner(),
                    "bb-20260820.4 · 2026-08-20 13:53"
                )
        finally:
            timezone.deactivate()

    def test_banner_unparseable_time_passthrough(self):
        # Garbage BB_BUILD_TIME renders verbatim rather than 500ing.
        with mock.patch.dict(os.environ, {
            "BB_BUILD_TAG": "bb-20260820.4",
            "BB_BUILD_TIME": "not-a-date",
        }):
            self.assertEqual(
                babybuddy.dev_build_banner(), "bb-20260820.4 · not-a-date"
            )


class DevBuildBannerRenderTestCase(TestCase):
    """The banner wiring in nav-dropdown.html renders on real pages."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="banneruser", password="bannerpass", is_superuser=True
        )

    def test_banner_renders_when_env_set(self):
        # User on America/New_York: the banner must render the build
        # time in the user's wall clock (13:53 EDT), not the baked UTC.
        self.user.settings.timezone = "America/New_York"
        self.user.settings.save()
        with mock.patch.dict(os.environ, {
            "BB_BUILD_TAG": "bb-20260820.4",
            "BB_BUILD_TIME": "2026-08-20 17:53 UTC",
        }):
            self.client.force_login(self.user)
            response = self.client.get("/feedings/")
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn("bb-20260820.4 · 2026-08-20 13:53", html)
            self.assertNotIn("17:53", html)
            # Official version header stays.
            self.assertIn("v", html)

    def test_banner_absent_when_env_unset(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BB_BUILD_TAG", None)
            self.client.force_login(self.user)
            response = self.client.get("/feedings/")
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("bb-20260820", response.content.decode())


class TemplateTagsTestCase(TestCase):
    def test_child_count(self):
        self.assertEqual(babybuddy.get_child_count(), 0)
        Child.objects.create(
            first_name="Test", last_name="Child", birth_date=timezone.localdate()
        )
        self.assertEqual(babybuddy.get_child_count(), 1)
        Child.objects.create(
            first_name="Test", last_name="Child 2", birth_date=timezone.localdate()
        )
        self.assertEqual(babybuddy.get_child_count(), 2)

    def test_user_is_read_only(self):
        user = get_user_model().objects.create_user(
            username="readonly", password="readonly", is_superuser=False, is_staff=False
        )
        self.assertFalse(babybuddy.user_is_read_only(user))

        group = Group.objects.get(name=settings.BABY_BUDDY["READ_ONLY_GROUP_NAME"])
        user.groups.add(group)
        self.assertTrue(babybuddy.user_is_read_only(user))
