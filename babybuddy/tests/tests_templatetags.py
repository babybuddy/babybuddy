# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.utils import timezone
from django.utils.translation import override

from core.models import Child
from babybuddy.templatetags import babybuddy


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

    def test_plotly_locale_code(self):
        self.assertEqual(babybuddy.plotly_locale_code("de"), "de")
        self.assertEqual(babybuddy.plotly_locale_code("pt-br"), "pt-br")
        self.assertEqual(babybuddy.plotly_locale_code("pt-BR"), "pt-br")
        self.assertEqual(babybuddy.plotly_locale_code("zh-hans"), "zh-cn")
        self.assertEqual(babybuddy.plotly_locale_code("nb"), "no")
        self.assertIsNone(babybuddy.plotly_locale_code("en-US"))
        self.assertIsNone(babybuddy.plotly_locale_code("en-us"))

    @override_settings(
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
            },
        }
    )
    def test_plotly_locale_script_omits_english(self):
        with override("en-US"):
            self.assertEqual(babybuddy.plotly_locale_script(), "")
        with override("fr"):
            html = babybuddy.plotly_locale_script()
            self.assertIn("plotly-locale-fr.js", html)
            self.assertIn("defer", html)
