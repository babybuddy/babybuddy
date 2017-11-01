# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory

from api.utils import filter_by_params
from core.models import Child


class UtilsTestCase(TestCase):
    def test_filter_by_params(self):
        factory = APIRequestFactory()

        Child.objects.create(
            first_name='First',
            last_name='Child',
            birth_date=timezone.localdate())
        Child.objects.create(
            first_name='Second',
            last_name='Child',
            birth_date=timezone.localdate())

        request = factory.get('/children/')
        request = APIView().initialize_request(request)
        response = filter_by_params(request, Child, [])
        self.assertTrue(response, Child.objects.all())

        request = factory.get('/children/', {'first_name': 'First'})
        request = APIView().initialize_request(request)
        response = filter_by_params(request, Child, ['first_name'])
        self.assertTrue(response, Child.objects.filter(first_name='First'))
