# -*- coding: utf-8 -*-
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from babybuddy.models import User
from core import models


class TestBase:

    class BabyBuddyAPITestCaseBase(APITestCase):
        fixtures = ['tests.json']
        model = None
        endpoint = None
        delete_id = 1
        timer_test_data = {}

        def setUp(self):
            self.client.login(username='admin', password='admin')

        def test_options(self):
            response = self.client.options(self.endpoint)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['name'], '{} List'.format(
                self.model._meta.verbose_name))

        def test_delete(self):
            endpoint = '{}{}/'.format(self.endpoint, self.delete_id)
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response = self.client.delete(endpoint)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        def test_post_with_timer(self):
            if not self.timer_test_data:
                return
            user = User.objects.first()
            start = timezone.now() - timezone.timedelta(minutes=10)
            timer = models.Timer.objects.create(user=user, start=start)
            self.timer_test_data['timer'] = timer.id

            if 'child' in self.timer_test_data:
                del self.timer_test_data['child']
            response = self.client.post(
                self.endpoint, self.timer_test_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            timer.refresh_from_db()
            self.assertTrue(timer.active)
            child = models.Child.objects.first()

            self.timer_test_data['child'] = child.id
            response = self.client.post(
                self.endpoint, self.timer_test_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            timer.refresh_from_db()
            self.assertFalse(timer.active)
            obj = self.model.objects.get(pk=response.data['id'])
            self.assertEqual(obj.start, start)
            self.assertEqual(obj.end, timer.end)

        def test_post_with_timer_with_child(self):
            if not self.timer_test_data:
                return
            user = User.objects.first()
            child = models.Child.objects.first()
            start = timezone.now() - timezone.timedelta(minutes=10)
            timer = models.Timer.objects.create(
                user=user, child=child, start=start)
            self.timer_test_data['timer'] = timer.id
            response = self.client.post(
                self.endpoint, self.timer_test_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            timer.refresh_from_db()
            self.assertFalse(timer.active)
            obj = self.model.objects.get(pk=response.data['id'])
            self.assertEqual(obj.child, timer.child)
            self.assertEqual(obj.start, start)
            self.assertEqual(obj.end, timer.end)


class ChildAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:child-list')
    model = models.Child
    delete_id = 'fake-child'

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 1,
            'first_name': 'Fake',
            'last_name': 'Child',
            'birth_date': '2017-11-11',
            'slug': 'fake-child',
            'picture': None
        })

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

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 'fake-child')
        response = self.client.get(endpoint)
        entry = response.data
        entry['first_name'] = 'New'
        entry['last_name'] = 'Name'
        response = self.client.patch(endpoint, {
            'first_name': entry['first_name'],
            'last_name': entry['last_name'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The slug we be updated by the name change.
        entry['slug'] = 'new-name'
        self.assertEqual(response.data, entry)


class DiaperChangeAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:diaperchange-list')
    model = models.DiaperChange
    delete_id = 3

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

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 3)
        response = self.client.get(endpoint)
        entry = response.data
        entry['wet'] = False
        entry['solid'] = True
        response = self.client.patch(endpoint, {
            'wet': entry['wet'],
            'solid': entry['solid'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class FeedingAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:feeding-list')
    model = models.Feeding
    timer_test_data = {'type': 'breast milk', 'method': 'left breast'}

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

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 3)
        response = self.client.get(endpoint)
        entry = response.data
        entry['type'] = 'breast milk'
        entry['method'] = 'left breast'
        entry['amount'] = 0
        response = self.client.patch(endpoint, {
            'type': entry['type'],
            'method': entry['method'],
            'amount': entry['amount'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class NoteAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:note-list')
    model = models.Note

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 1,
            'child': 1,
            'note': 'Fake note.',
            'time': '2017-11-17T22:45:00-05:00'
        })

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

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 1)
        response = self.client.get(endpoint)
        entry = response.data
        entry['note'] = 'Updated note text.'
        response = self.client.patch(endpoint, {
            'note': entry['note'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The time of entry will always update automatically, so only check the
        # new value.
        self.assertEqual(response.data['note'], entry['note'])


class SleepAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:sleep-list')
    model = models.Sleep
    timer_test_data = {'child': 1}

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 4,
            'child': 1,
            'start': '2017-11-18T19:00:00-05:00',
            'end': '2017-11-18T23:00:00-05:00',
            'duration': '04:00:00',
            'nap': False
        })

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

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 4)
        response = self.client.get(endpoint)
        entry = response.data
        entry['end'] = '2017-11-18T23:30:00-05:00'
        response = self.client.patch(endpoint, {
            'end': entry['end'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The duration of entry will always update automatically, so only check
        # the new value.
        self.assertEqual(response.data['end'], entry['end'])


class TemperatureAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:temperature-list')
    model = models.Temperature

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 1,
            'child': 1,
            'temperature': 98.6,
            'time': '2017-11-17T12:52:00-05:00'
        })

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

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 1)
        response = self.client.get(endpoint)
        entry = response.data
        entry['temperature'] = 99
        response = self.client.patch(endpoint, {
            'temperature': entry['temperature'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class TimerAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:timer-list')
    model = models.Timer

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 1,
            'child': None,
            'name': 'Fake timer',
            'start': '2017-11-17T23:30:00-05:00',
            'end': '2017-11-18T00:30:00-05:00',
            'duration': '01:00:00',
            'active': False,
            'user': 1
        })

    def test_post(self):
        data = {
            'name': 'New fake timer',
            'user': 1
        }
        response = self.client.post(self.endpoint, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Timer.objects.get(pk=response.data['id'])
        self.assertEqual(obj.name, data['name'])

    def test_post_default_user(self):
        user = User.objects.first()
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Timer.objects.get(pk=response.data['id'])
        self.assertEqual(obj.user, user)

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 1)
        response = self.client.get(endpoint)
        entry = response.data
        entry['name'] = 'New Timer Name'
        response = self.client.patch(endpoint, {
            'name': entry['name'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class TummyTimeAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:tummytime-list')
    model = models.TummyTime
    timer_test_data = {'milestone': 'Timer test'}

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

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 3)
        response = self.client.get(endpoint)
        entry = response.data
        entry['milestone'] = 'Switched sides!'
        response = self.client.patch(endpoint, {
            'milestone': entry['milestone'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class WeightAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse('api:weight-list')
    model = models.Weight

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0], {
            'id': 2,
            'child': 1,
            'weight': 9.5,
            'date': '2017-11-18'
        })

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

    def test_patch(self):
        endpoint = '{}{}/'.format(self.endpoint, 2)
        response = self.client.get(endpoint)
        entry = response.data
        entry['weight'] = 8.25
        response = self.client.patch(endpoint, {
            'weight': entry['weight'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)
