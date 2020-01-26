# -*- coding: utf-8 -*-
from django.test import override_settings
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from core import models


@override_settings(TIME_ZONE='US/Eastern')
class ChildAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:child-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 1,
            'first_name': 'Fake',
            'last_name': 'Child',
            'birth_date': '2017-11-11',
            'slug': 'fake-child'
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Child List')

    def test_post(self):
        data = {
            'first_name': 'Test',
            'last_name': 'Child',
            'birth_date': '2017-11-12'
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Child.objects.get(pk=response.data['id'])
        self.assertEqual(obj.first_name, data['first_name'])


@override_settings(TIME_ZONE='US/Eastern')
class DiaperChangeAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:diaperchange-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 3,
            'child': 1,
            'time': '2017-11-18T14:00:00-05:00',
            'wet': True,
            'solid': False,
            'color': '',
            'amount': 2.25
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Diaper Change List')

    def test_post(self):
        data = {
            'child': 1,
            'time': '2017-11-18T12:00:00-05:00',
            'wet': True,
            'solid': True,
            'color': 'brown',
            'amount': 1.25
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.DiaperChange.objects.get(pk=response.data['id'])
        self.assertTrue(obj.wet)
        self.assertTrue(obj.solid)
        self.assertEqual(obj.color, data['color'])
        self.assertEqual(obj.amount, data['amount'])


@override_settings(TIME_ZONE='US/Eastern')
class FeedingAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:feeding-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 3,
            'child': 1,
            'start': '2017-11-18T14:00:00-05:00',
            'end': '2017-11-18T14:15:00-05:00',
            'duration': '00:15:00',
            'type': 'formula',
            'method': 'bottle',
            'amount': 2.5
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Feeding List')

    def test_post(self):
        data = {
            'child': 1,
            'start': '2017-11-19T14:00:00-05:00',
            'end': '2017-11-19T14:15:00-05:00',
            'type': 'breast milk',
            'method': 'left breast'
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Feeding.objects.get(pk=response.data['id'])
        self.assertEqual(obj.type, data['type'])


@override_settings(TIME_ZONE='US/Eastern')
class NoteAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:note-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 1,
            'child': 1,
            'note': 'Fake note.',
            'time': '2017-11-17T22:45:00-05:00'
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Note List')

    def test_post(self):
        data = {
            'child': 1,
            'note': 'New fake note.',
            'time': '2017-11-18T22:45:00-05:00'
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Note.objects.get(pk=response.data['id'])
        self.assertEqual(obj.note, data['note'])


@override_settings(TIME_ZONE='US/Eastern')
class SleepAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:sleep-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 4,
            'child': 1,
            'start': '2017-11-18T19:00:00-05:00',
            'end': '2017-11-18T23:00:00-05:00',
            'duration': '04:00:00'
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Sleep List')

    def test_post(self):
        data = {
            'child': 1,
            'start': '2017-11-21T19:30:00-05:00',
            'end': '2017-11-21T23:00:00-05:00',
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Sleep.objects.get(pk=response.data['id'])
        self.assertEqual(str(obj.duration), '3:30:00')


@override_settings(TIME_ZONE='US/Eastern')
class TemperatureAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:temperature-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 1,
            'child': 1,
            'temperature': 98.6,
            'time': '2017-11-17T12:52:00-05:00'
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Temperature List')

    def test_post(self):
        data = {
            'child': 1,
            'temperature': '100.1',
            'time': '2017-11-20T22:52:00-05:00'
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Temperature.objects.get(pk=response.data['id'])
        self.assertEqual(str(obj.temperature), data['temperature'])


@override_settings(TIME_ZONE='US/Eastern')
class TimerAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:timer-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 1,
            'name': 'Fake timer',
            'start': '2017-11-17T23:30:00-05:00',
            'end': '2017-11-18T00:30:00-05:00',
            'duration': '01:00:00',
            'active': False,
            'user': 1
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Timer List')

    def test_post(self):
        data = {
            'name': 'New fake timer',
            'user': 1
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Timer.objects.get(pk=response.data['id'])
        self.assertEqual(obj.name, data['name'])


@override_settings(TIME_ZONE='US/Eastern')
class TummyTimeAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:tummytime-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 3,
            'child': 1,
            'start': '2017-11-18T15:30:00-05:00',
            'end': '2017-11-18T15:30:45-05:00',
            'duration': '00:00:45',
            'milestone': ''
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Tummy Time List')

    def test_post(self):
        data = {
            'child': 1,
            'start': '2017-11-18T12:30:00-05:00',
            'end': '2017-11-18T12:35:30-05:00',
            'milestone': 'Rolled over.'
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.TummyTime.objects.get(pk=response.data['id'])
        self.assertEqual(str(obj.duration), '0:05:30')


@override_settings(TIME_ZONE='US/Eastern')
class WeightAPITestCase(APITestCase):
    fixtures = ['tests.json']
    endpoint = reverse('api:weight-list')

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 2,
            'child': 1,
            'weight': 9.5,
            'date': '2017-11-18'
        })

    def test_options(self):
        response = self.client.options(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Weight List')

    def test_post(self):
        data = {
            'child': 1,
            'weight': '9.75',
            'date': '2017-11-20'
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Weight.objects.get(pk=response.data['id'])
        self.assertEqual(str(obj.weight), data['weight'])
