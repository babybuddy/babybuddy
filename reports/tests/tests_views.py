# -*- coding: utf-8 -*-
from django.test import TestCase
from django.test import Client as HttpClient
from django.contrib.auth.models import User
from django.core.management import call_command

from faker import Factory

from core import models


class ViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(ViewsTestCase, cls).setUpClass()
        fake = Factory.create()
        call_command('migrate', verbosity=0)
        call_command('fake', verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        cls.credentials = {
            'username': fake_user['username'],
            'password': fake.password()
        }
        cls.user = User.objects.create_user(
            is_superuser=True, **cls.credentials)

        cls.c.login(**cls.credentials)

    def test_graph_child_views(self):
        child = models.Child.objects.first()
        base_url = '/children/{}/reports'.format(child.slug)

        page = self.c.get('{}/changes/amounts/'.format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('{}/changes/lifetimes/'.format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('{}/changes/types/'.format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get('{}/feeding/amounts/'.format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('{}/feeding/duration/'.format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get('{}/sleep/pattern/'.format(base_url))
        self.assertEqual(page.status_code, 200)
        page = self.c.get('{}/sleep/totals/'.format(base_url))
        self.assertEqual(page.status_code, 200)

        page = self.c.get('{}/weight/weight/'.format(base_url))
        self.assertEqual(page.status_code, 200)
