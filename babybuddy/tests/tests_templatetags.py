# -*- coding: utf-8 -*-
from django.test import TestCase
from django.utils import timezone

from core.models import Child
from babybuddy.templatetags import babybuddy_tags


class TemplateTagsTestCase(TestCase):
    def test_child_count(self):
        self.assertEqual(babybuddy_tags.get_child_count(), 0)
        Child.objects.create(first_name='Test', last_name='Child',
                             birth_date=timezone.localdate())
        self.assertEqual(babybuddy_tags.get_child_count(), 1)
        Child.objects.create(first_name='Test', last_name='Child 2',
                             birth_date=timezone.localdate())
        self.assertEqual(babybuddy_tags.get_child_count(), 2)
