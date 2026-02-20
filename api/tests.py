# -*- coding: utf-8 -*-
from babybuddy.models import get_user_model
from core import models
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase


class TestBase:
    class BabyBuddyAPITestCaseBase(APITestCase):
        fixtures = ["tests.json"]
        model = None
        endpoint = None
        delete_id = 1
        timer_test_data = {}

        def setUp(self):
            self.client.login(username="admin", password="admin")

        def test_options(self):
            response = self.client.options(self.endpoint)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(
                response.data["name"], "{} List".format(self.model._meta.verbose_name)
            )

        def test_delete(self):
            endpoint = "{}{}/".format(self.endpoint, self.delete_id)
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response = self.client.delete(endpoint)
            self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        def test_post_with_timer(self):
            if not self.timer_test_data:
                return
            user = get_user_model().objects.first()
            start = timezone.now() - timezone.timedelta(minutes=10)
            timer = models.Timer.objects.create(user=user, start=start)
            self.timer_test_data["timer"] = timer.id

            if "child" in self.timer_test_data:
                del self.timer_test_data["child"]
            response = self.client.post(
                self.endpoint, self.timer_test_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            timer.refresh_from_db()
            child = models.Child.objects.first()

            self.timer_test_data["child"] = child.id
            response = self.client.post(
                self.endpoint, self.timer_test_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            obj = self.model.objects.get(pk=response.data["id"])
            self.assertEqual(obj.start, start)
            self.assertIsNotNone(obj.end)

        def test_post_with_timer_with_child(self):
            if not self.timer_test_data:
                return
            user = get_user_model().objects.first()
            child = models.Child.objects.first()
            start = timezone.now() - timezone.timedelta(minutes=10)
            timer = models.Timer.objects.create(user=user, child=child, start=start)
            self.timer_test_data["timer"] = timer.id
            response = self.client.post(
                self.endpoint, self.timer_test_data, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            obj = self.model.objects.get(pk=response.data["id"])
            self.assertIsNotNone(obj.child)
            self.assertEqual(obj.start, start)
            self.assertIsNotNone(obj.end)


class BMIAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:bmi-list")
    model = models.BMI

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 2,
                "child": 1,
                "bmi": 26.5,
                "date": "2017-11-18",
                "notes": "before feed",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "bmi": "27.0",
            "date": "2017-11-15",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = self.model.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.bmi), data["bmi"])

    def test_post_null_date(self):
        data = {"child": 1, "bmi": "12.25"}
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = self.model.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.bmi), data["bmi"])
        self.assertEqual(str(obj.date), timezone.localdate().strftime("%Y-%m-%d"))

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 2)
        response = self.client.get(endpoint)
        entry = response.data
        entry["bmi"] = 30.0
        response = self.client.patch(endpoint, {"bmi": entry["bmi"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class ChildAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:child-list")
    model = models.Child
    delete_id = "fake-child"

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 1,
                "first_name": "Fake",
                "last_name": "Child",
                "birth_date": "2017-11-11",
                "birth_time": None,
                "slug": "fake-child",
                "picture": None,
            },
        )

    def test_post(self):
        data = {
            "first_name": "Test",
            "last_name": "Child",
            "birth_date": "2017-11-12",
            "birth_time": "23:25",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Child.objects.get(pk=response.data["id"])
        self.assertEqual(obj.first_name, data["first_name"])

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, "fake-child")
        response = self.client.get(endpoint)
        entry = response.data
        entry["first_name"] = "New"
        entry["last_name"] = "Name"
        response = self.client.patch(
            endpoint,
            {
                "first_name": entry["first_name"],
                "last_name": entry["last_name"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The slug we be updated by the name change.
        entry["slug"] = "new-name"
        self.assertEqual(response.data, entry)


class PumpingAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:pumping-list")
    model = models.Pumping
    timer_test_data = {"amount": 2}

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 2,
                "child": 1,
                "amount": 9.0,
                "start": "2017-11-17T15:03:00-05:00",
                "end": "2017-11-17T15:22:00-05:00",
                "duration": "00:19:00",
                "notes": "new device",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "amount": "21.0",
            "start": "2017-11-20T22:52:00-05:00",
            "end": "2017-11-20T23:05:00-05:00",
            "notes": "old device",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Pumping.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.amount), data["amount"])
        self.assertEqual(obj.notes, data["notes"])

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 1)
        response = self.client.get(endpoint)
        entry = response.data
        entry["amount"] = 41
        response = self.client.patch(
            endpoint,
            {
                "amount": entry["amount"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class DiaperChangeAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:diaperchange-list")
    model = models.DiaperChange
    delete_id = 3

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 3,
                "child": 1,
                "time": "2017-11-18T14:00:00-05:00",
                "wet": True,
                "solid": False,
                "color": "",
                "amount": 2.25,
                "notes": "stinky",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "time": "2017-11-18T12:00:00-05:00",
            "wet": True,
            "solid": True,
            "color": "brown",
            "amount": 1.25,
            "notes": "seedy",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.DiaperChange.objects.get(pk=response.data["id"])
        self.assertTrue(obj.wet)
        self.assertTrue(obj.solid)
        self.assertEqual(obj.color, data["color"])
        self.assertEqual(obj.amount, data["amount"])
        self.assertEqual(obj.notes, data["notes"])

    def test_post_null_time(self):
        data = {
            "child": 1,
            "wet": False,
            "solid": True,
            "color": "black",
            "amount": 3,
            "notes": "noxious",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.DiaperChange.objects.get(pk=response.data["id"])
        self.assertFalse(obj.wet)
        self.assertTrue(obj.solid)
        self.assertEqual(obj.color, data["color"])
        self.assertEqual(obj.amount, data["amount"])
        self.assertEqual(obj.notes, data["notes"])

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 3)
        response = self.client.get(endpoint)
        entry = response.data
        entry["wet"] = False
        entry["solid"] = True
        response = self.client.patch(
            endpoint,
            {
                "wet": entry["wet"],
                "solid": entry["solid"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class FeedingAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:feeding-list")
    model = models.Feeding
    timer_test_data = {"type": "breast milk", "method": "left breast"}

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 3,
                "child": 1,
                "start": "2017-11-18T09:00:00-05:00",
                "end": "2017-11-18T09:15:00-05:00",
                "duration": "00:15:00",
                "type": "formula",
                "method": "bottle",
                "amount": 2.5,
                "notes": "forgot vitamins :(",
                "tags": [],
            },
        )

    # check backwards compatibility
    def test_get_with_date_filter(self):
        response = self.client.get(self.endpoint, {"start_min": "2017-11-18"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_get_with_iso_filter(self):
        response = self.client.get(
            self.endpoint, {"start_min": "2017-11-18T04:00:00-05:00"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_post(self):
        data = {
            "child": 1,
            "start": "2017-11-19T14:00:00-05:00",
            "end": "2017-11-19T14:15:00-05:00",
            "type": "breast milk",
            "method": "left breast",
            "notes": "with vitamins",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Feeding.objects.get(pk=response.data["id"])
        self.assertEqual(obj.type, data["type"])
        self.assertEqual(obj.notes, data["notes"])

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 3)
        response = self.client.get(endpoint)
        entry = response.data
        entry["type"] = "breast milk"
        entry["method"] = "left breast"
        entry["amount"] = 0
        response = self.client.patch(
            endpoint,
            {
                "type": entry["type"],
                "method": entry["method"],
                "amount": entry["amount"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class HeadCircumferenceAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:headcircumference-list")
    model = models.HeadCircumference

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 2,
                "child": 1,
                "head_circumference": 6.5,
                "date": "2017-11-18",
                "notes": "before feed",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "head_circumference": "9.5",
            "date": "2017-11-15",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = self.model.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.head_circumference), data["head_circumference"])

    def test_post_null_date(self):
        data = {"child": 1, "head_circumference": "10.0"}
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = self.model.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.head_circumference), data["head_circumference"])
        self.assertEqual(str(obj.date), timezone.localdate().strftime("%Y-%m-%d"))

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 2)
        response = self.client.get(endpoint)
        entry = response.data
        entry["head_circumference"] = 23
        response = self.client.patch(
            endpoint, {"head_circumference": entry["head_circumference"]}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class HeightAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:height-list")
    model = models.Height

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 2,
                "child": 1,
                "height": 10.5,
                "date": "2017-11-18",
                "notes": "before feed",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "height": "12.5",
            "date": "2017-11-15",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = self.model.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.height), data["height"])

    def test_post_null_date(self):
        data = {"child": 1, "height": "19.0"}
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = self.model.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.height), data["height"])
        self.assertEqual(str(obj.date), timezone.localdate().strftime("%Y-%m-%d"))

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 2)
        response = self.client.get(endpoint)
        entry = response.data
        entry["height"] = 23.5
        response = self.client.patch(endpoint, {"height": entry["height"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class NoteAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:note-list")
    model = models.Note

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.data["results"][0],
            {
                "id": 1,
                "child": 1,
                "note": "Fake note.",
                "image": None,
                "time": "2017-11-17T22:45:00-05:00",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "note": "New fake note.",
            "time": "2017-11-18T22:45:00-05:00",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Note.objects.get(pk=response.data["id"])
        self.assertEqual(obj.note, data["note"])

    def test_post_null_time(self):
        data = {
            "child": 1,
            "note": "Another fake note.",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Note.objects.get(pk=response.data["id"])
        self.assertEqual(obj.note, data["note"])

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 1)
        response = self.client.get(endpoint)
        entry = response.data
        entry["note"] = "Updated note text."
        response = self.client.patch(
            endpoint,
            {
                "note": entry["note"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The time of entry will always update automatically, so only check the
        # new value.
        self.assertEqual(response.data["note"], entry["note"])


class SleepAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:sleep-list")
    model = models.Sleep
    timer_test_data = {"child": 1}

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.data["results"][0],
            {
                "id": 4,
                "child": 1,
                "start": "2017-11-19T03:00:00-05:00",
                "end": "2017-11-19T04:30:00-05:00",
                "duration": "01:30:00",
                "nap": True,
                "notes": "lots of squirming",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "start": "2017-11-21T19:30:00-05:00",
            "end": "2017-11-21T23:00:00-05:00",
            "notes": "used new swaddle",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Sleep.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.duration), "3:30:00")
        self.assertEqual(obj.notes, data["notes"])

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 4)
        response = self.client.get(endpoint)
        entry = response.data
        entry["end"] = "2017-11-19T08:30:00-05:00"
        response = self.client.patch(
            endpoint,
            {
                "end": entry["end"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The duration of entry will always update automatically, so only check
        # the new value.
        self.assertEqual(response.data["end"], entry["end"])


class TagsAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:tag-list")
    model = models.Tag

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            dict(response.data["results"][0]),
            {
                "name": "a name",
                "slug": "a-name",
                "color": "#FF0000",
                "last_used": "2017-11-18T11:00:00-05:00",
            },
        )

    def test_post(self):
        data = {"name": "new tag", "color": "#123456"}
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get(self.endpoint)
        results = response.json()["results"]
        results_by_name = {r["name"]: r for r in results}

        tag_data = results_by_name["new tag"]
        self.assertEqual(tag_data, tag_data | data)
        self.assertEqual(tag_data["slug"], "new-tag")
        self.assertTrue(tag_data["last_used"])

    def test_patch(self):
        endpoint = f"{self.endpoint}a-name/"

        modified_data = {
            "name": "A different name",
            "color": "#567890",
        }
        response = self.client.patch(
            endpoint,
            modified_data,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, response.data | modified_data)

    def test_delete(self):
        endpoint = f"{self.endpoint}a-name/"
        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_post_tags_to_model(self):
        data = {"child": 1, "note": "New tagged note.", "tags": ["tag1", "tag2"]}
        response = self.client.post(reverse("api:note-list"), data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertCountEqual(response.data["tags"], data["tags"])
        note = models.Note.objects.get(pk=response.data["id"])
        self.assertCountEqual(list(note.tags.names()), data["tags"])


class MedicationAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:medication-list")
    model = models.Medication
    delete_id = None  # Overridden in setUp

    def setUp(self):
        super().setUp()
        child = models.Child.objects.first()
        self.med = models.Medication.objects.create(
            child=child,
            name="Vitamin D",
            amount=400,
            amount_unit="IU",
            time="2017-11-18T12:00:00-05:00",
        )
        self.delete_id = self.med.id

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)
        result = response.data["results"][0]
        self.assertEqual(result["name"], "Vitamin D")

    def test_post(self):
        data = {
            "child": 1,
            "name": "Ibuprofen",
            "amount": 100,
            "amount_unit": "mg",
            "time": "2017-11-20T10:00:00-05:00",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Medication.objects.get(pk=response.data["id"])
        self.assertEqual(obj.name, "Ibuprofen")
        self.assertEqual(obj.amount, 100)

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, self.med.id)
        response = self.client.patch(endpoint, {"name": "Updated Med"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Med")

    def test_delete(self):
        endpoint = "{}{}/".format(self.endpoint, self.med.id)
        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MedicationScheduleAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:medicationschedule-list")
    model = models.MedicationSchedule
    delete_id = None

    def setUp(self):
        super().setUp()
        child = models.Child.objects.first()
        self.schedule = models.MedicationSchedule.objects.create(
            child=child,
            name="Vitamin D",
            amount=400,
            amount_unit="IU",
            frequency="daily",
            schedule_time="09:00:00",
            active=True,
        )
        self.delete_id = self.schedule.id

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data["results"]), 0)
        result = response.data["results"][0]
        self.assertEqual(result["name"], "Vitamin D")
        self.assertEqual(result["frequency"], "daily")

    def test_post(self):
        data = {
            "child": 1,
            "name": "Ibuprofen",
            "frequency": "interval",
            "interval_hours": 6,
            "active": True,
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.MedicationSchedule.objects.get(pk=response.data["id"])
        self.assertEqual(obj.name, "Ibuprofen")
        self.assertEqual(obj.frequency, "interval")

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, self.schedule.id)
        response = self.client.patch(endpoint, {"active": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["active"])

    def test_delete(self):
        endpoint = "{}{}/".format(self.endpoint, self.schedule.id)
        response = self.client.delete(endpoint)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TemperatureAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:temperature-list")
    model = models.Temperature

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 1,
                "child": 1,
                "temperature": 98.6,
                "time": "2017-11-17T12:52:00-05:00",
                "notes": "tympanic",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "temperature": "100.1",
            "time": "2017-11-20T22:52:00-05:00",
            "notes": "rectal",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Temperature.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.temperature), data["temperature"])
        self.assertEqual(obj.notes, data["notes"])

    def test_post_null_time(self):
        data = {
            "child": 1,
            "temperature": "100.5",
            "notes": "temporal",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Temperature.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.temperature), data["temperature"])
        self.assertEqual(obj.notes, data["notes"])

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 1)
        response = self.client.get(endpoint)
        entry = response.data
        entry["temperature"] = 99
        response = self.client.patch(
            endpoint,
            {
                "temperature": entry["temperature"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class TimerAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:timer-list")
    model = models.Timer

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["id"], 1)

    def test_post(self):
        data = {"name": "New fake timer", "user": 1}
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Timer.objects.get(pk=response.data["id"])
        self.assertEqual(obj.name, data["name"])

    def test_post_default_user(self):
        user = get_user_model().objects.first()
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Timer.objects.get(pk=response.data["id"])
        self.assertEqual(obj.user, user)

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 1)
        response = self.client.get(endpoint)
        entry = response.data
        entry["name"] = "New Timer Name"
        response = self.client.patch(
            endpoint,
            {
                "name": entry["name"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], entry["name"])

    def test_start_restart_timer(self):
        endpoint = "{}{}/".format(self.endpoint, 1)
        response = self.client.get(endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.patch(f"{endpoint}restart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Restart twice is allowed
        response = self.client.patch(f"{endpoint}restart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TummyTimeAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:tummytime-list")
    model = models.TummyTime
    timer_test_data = {"milestone": "Timer test"}

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 3,
                "child": 1,
                "start": "2017-11-18T15:30:00-05:00",
                "end": "2017-11-18T15:30:45-05:00",
                "duration": "00:00:45",
                "milestone": "",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "start": "2017-11-18T12:30:00-05:00",
            "end": "2017-11-18T12:35:30-05:00",
            "milestone": "Rolled over.",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.TummyTime.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.duration), "0:05:30")

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 3)
        response = self.client.get(endpoint)
        entry = response.data
        entry["milestone"] = "Switched sides!"
        response = self.client.patch(
            endpoint,
            {
                "milestone": entry["milestone"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class WeightAPITestCase(TestBase.BabyBuddyAPITestCaseBase):
    endpoint = reverse("api:weight-list")
    model = models.Weight

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["results"][0],
            {
                "id": 2,
                "child": 1,
                "weight": 9.5,
                "date": "2017-11-18",
                "notes": "before feed",
                "tags": [],
            },
        )

    def test_post(self):
        data = {
            "child": 1,
            "weight": "9.75",
            "date": "2017-11-20",
            "notes": "after feed",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Weight.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.weight), data["weight"])
        self.assertEqual(str(obj.notes), data["notes"])

    def test_post_null_date(self):
        data = {
            "child": 1,
            "weight": "12.25",
            "notes": "with diaper at peds",
        }
        response = self.client.post(self.endpoint, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        obj = models.Weight.objects.get(pk=response.data["id"])
        self.assertEqual(str(obj.weight), data["weight"])
        self.assertEqual(str(obj.notes), data["notes"])

    def test_patch(self):
        endpoint = "{}{}/".format(self.endpoint, 2)
        response = self.client.get(endpoint)
        entry = response.data
        entry["weight"] = 8.25
        response = self.client.patch(
            endpoint,
            {
                "weight": entry["weight"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, entry)


class TestProfileAPITestCase(APITestCase):
    endpoint = reverse("api:profile")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_get(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            response.data,
            response.data
            | {
                "language": "en-US",
                "timezone": "UTC",
            },
        )
        self.assertEqual(
            response.data["user"],
            response.data["user"]
            | {
                "id": 1,
                "username": "admin",
                "first_name": "",
                "last_name": "",
                "email": "",
                "is_staff": True,
            },
        )
        # Test that api_key is in the mix and "some long string"
        self.assertIn("api_key", response.data)
        self.assertTrue(isinstance(response.data["api_key"], str))
        self.assertGreater(len(response.data["api_key"]), 30)


class TestHADiscoveryView(APITestCase):
    endpoint = reverse("api:ha-discovery")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_version(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["version"], 2)

    def test_top_level_keys(self):
        response = self.client.get(self.endpoint)
        expected_keys = {
            "version",
            "api",
            "child",
            "timer",
            "transforms",
            "mqtt",
            "sensors",
            "stats_sensors",
            "binary_sensors",
            "selects",
            "services",
        }
        self.assertEqual(set(response.data.keys()), expected_keys)

    def test_api_section(self):
        response = self.client.get(self.endpoint)
        api = response.data["api"]
        self.assertEqual(api["child_filter_param"], "child")
        self.assertEqual(api["limit_param"], "limit")
        self.assertIn("list_response_format", api)
        self.assertIn("stats_endpoint", api)

    def test_child_section(self):
        response = self.client.get(self.endpoint)
        child = response.data["child"]
        self.assertEqual(child["icon"], "mdi:baby-face-outline")
        self.assertEqual(child["state_field"], "birth_date")
        self.assertIn("fields", child)
        self.assertIn("slug", child["fields"])

    def test_timer_section(self):
        response = self.client.get(self.endpoint)
        timer = response.data["timer"]
        self.assertEqual(timer["endpoint"], "timers")
        self.assertEqual(timer["active_detection"], "presence")

    def test_transforms_section(self):
        response = self.client.get(self.endpoint)
        transforms = response.data["transforms"]
        self.assertIn("diaper_type_to_booleans", transforms)
        self.assertIn("lowercase", transforms)
        self.assertEqual(transforms["lowercase"]["operation"], "lowercase")
        mapping = transforms["diaper_type_to_booleans"]
        self.assertTrue(mapping["removes_field"])
        self.assertIn("Wet", mapping["mapping"])

    def test_mqtt_topic_patterns(self):
        response = self.client.get(self.endpoint)
        mqtt = response.data["mqtt"]
        self.assertIn("topic_pattern", mqtt)
        self.assertIn("stats_topic_pattern", mqtt)
        self.assertEqual(
            mqtt["topic_pattern"],
            "{prefix}/{child_slug}/{data_type}/state",
        )
        self.assertIn("topics", mqtt)

    def test_selects_includes_medication_units(self):
        response = self.client.get(self.endpoint)
        selects = response.data["selects"]
        self.assertEqual(len(selects), 5)
        med_units = next(s for s in selects if s["key"] == "medication_units")
        self.assertFalse(med_units["entity"])
        self.assertIn("ml", med_units["options"])

    def test_services_count_and_structure(self):
        response = self.client.get(self.endpoint)
        services = response.data["services"]
        self.assertEqual(len(services), 16)
        keys = [s["key"] for s in services]
        self.assertIn("add_child", keys)
        self.assertIn("add_feeding", keys)
        self.assertIn("delete_last_entry", keys)
        self.assertIn("start_timer", keys)
        self.assertIn("give_medication", keys)

    def test_service_add_feeding_detail(self):
        response = self.client.get(self.endpoint)
        services = response.data["services"]
        feeding = next(s for s in services if s["key"] == "add_feeding")
        self.assertTrue(feeding["uses_timer"])
        self.assertTrue(feeding["common_fields"])
        self.assertIn("type", feeding["fields"])
        self.assertEqual(feeding["fields"]["type"]["select_key"], "feeding_type")
        self.assertIn("transforms", feeding)
        self.assertEqual(feeding["transforms"]["type"], "lowercase")

    def test_service_delete_last_entry(self):
        response = self.client.get(self.endpoint)
        services = response.data["services"]
        delete = next(s for s in services if s["key"] == "delete_last_entry")
        self.assertEqual(delete["method"], "DELETE")
        self.assertIsNone(delete["endpoint"])

    def test_field_name_and_description(self):
        """Every service field should have name and description."""
        response = self.client.get(self.endpoint)
        for svc in response.data["services"]:
            for field_key, field_def in svc["fields"].items():
                self.assertIn(
                    "name",
                    field_def,
                    f"Service {svc['key']}, field {field_key} missing 'name'",
                )
                self.assertIn(
                    "description",
                    field_def,
                    f"Service {svc['key']}, field {field_key} missing 'description'",
                )

    def test_field_selector_hints(self):
        """Number fields should have selector_hints with appropriate ranges."""
        response = self.client.get(self.endpoint)
        services = response.data["services"]
        temp = next(s for s in services if s["key"] == "add_temperature")
        hints = temp["fields"]["temperature"]["selector_hints"]
        self.assertEqual(hints["min"], 35.0)
        self.assertEqual(hints["max"], 150.0)
        self.assertEqual(hints["step"], 0.1)

        bmi = next(s for s in services if s["key"] == "add_bmi")
        hints = bmi["fields"]["bmi"]["selector_hints"]
        self.assertEqual(hints["min"], 0.1)
        self.assertEqual(hints["max"], 100.0)

        weight = next(s for s in services if s["key"] == "add_weight")
        hints = weight["fields"]["weight"]["selector_hints"]
        self.assertNotIn("max", hints)

        give_med = next(s for s in services if s["key"] == "give_medication")
        hints = give_med["fields"]["schedule_id"]["selector_hints"]
        self.assertEqual(hints["min"], 1)

    def test_field_multiline(self):
        """String fields for notes/milestone should have multiline: True."""
        response = self.client.get(self.endpoint)
        services = response.data["services"]
        feeding = next(s for s in services if s["key"] == "add_feeding")
        self.assertTrue(feeding["fields"]["notes"]["multiline"])

        note_svc = next(s for s in services if s["key"] == "add_note")
        self.assertTrue(note_svc["fields"]["note"]["multiline"])

        tummy = next(s for s in services if s["key"] == "add_tummy_time")
        self.assertTrue(tummy["fields"]["milestone"]["multiline"])

        # Non-multiline string fields should not have the key
        child_svc = next(s for s in services if s["key"] == "add_child")
        self.assertNotIn("multiline", child_svc["fields"]["first_name"])

    def test_field_entity_domain(self):
        """entity_id fields should specify entity_domain."""
        response = self.client.get(self.endpoint)
        services = response.data["services"]
        delete = next(s for s in services if s["key"] == "delete_last_entry")
        self.assertEqual(delete["fields"]["entity_id"]["entity_domain"], "sensor")

        start_timer = next(s for s in services if s["key"] == "start_timer")
        self.assertEqual(start_timer["fields"]["child"]["entity_domain"], "switch")

        give_med = next(s for s in services if s["key"] == "give_medication")
        self.assertEqual(give_med["fields"]["child"]["entity_domain"], "sensor")

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestMQTTDiscoverView(APITestCase):
    endpoint = reverse("api:mqtt-discover")

    def setUp(self):
        self.client.login(username="admin", password="admin")

    def test_returns_list(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_broker_entry_structure(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for broker in response.data:
            self.assertIn("host", broker)
            self.assertIn("port", broker)
            self.assertIn("source", broker)

    def test_requires_auth(self):
        self.client.logout()
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
