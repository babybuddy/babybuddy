# -*- coding: utf-8 -*-
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.test import Client as HttpClient
from django.utils import timezone

from faker import Faker

from core import models


class ViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(ViewsTestCase, cls).setUpClass()
        fake = Faker()
        call_command("migrate", verbosity=0)
        call_command("fake", verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        cls.credentials = {
            "username": fake_user["username"],
            "password": fake.password(),
        }
        cls.user = get_user_model().objects.create_user(
            is_superuser=True, **cls.credentials
        )

        cls.c.login(**cls.credentials)

    def test_bmi_views(self):
        page = self.c.get("/bmi/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/bmi/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.BMI.objects.first()
        page = self.c.get("/bmi/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/bmi/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_child_views(self):
        page = self.c.get("/children/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/children/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Child.objects.first()
        page = self.c.get("/children/{}/".format(entry.slug))
        self.assertEqual(page.status_code, 200)
        page = self.c.get(
            "/children/{}/".format(entry.slug),
            {"date": timezone.localdate() - timezone.timedelta(days=1)},
        )
        self.assertEqual(page.status_code, 200)

        page = self.c.get("/children/{}/edit/".format(entry.slug))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/children/{}/delete/".format(entry.slug))
        self.assertEqual(page.status_code, 200)

    def test_diaperchange_views(self):
        page = self.c.get("/changes/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/changes/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.DiaperChange.objects.first()
        page = self.c.get("/changes/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/changes/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_feeding_views(self):
        page = self.c.get("/feedings/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/feedings/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Feeding.objects.first()
        page = self.c.get("/feedings/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/feedings/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_headcircumference_views(self):
        page = self.c.get("/head-circumference/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/head-circumference/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.HeadCircumference.objects.first()
        page = self.c.get("/head-circumference/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/head-circumference/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_height_views(self):
        page = self.c.get("/height/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/height/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Height.objects.first()
        page = self.c.get("/height/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/height/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_note_views(self):
        page = self.c.get("/notes/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/notes/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Note.objects.first()
        page = self.c.get("/notes/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/notes/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_pumping_views(self):
        page = self.c.get("/pumping/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/pumping/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Pumping.objects.first()
        page = self.c.get("/pumping/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/pumping/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_sleep_views(self):
        page = self.c.get("/sleep/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/sleep/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Sleep.objects.first()
        page = self.c.get("/sleep/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/sleep/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_temperature_views(self):
        page = self.c.get("/temperature/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/temperature/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Temperature.objects.first()
        page = self.c.get("/temperature/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/temperature/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_timer_views(self):
        page = self.c.get("/timers/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/timers/add/")
        self.assertEqual(page.status_code, 200)

        page = self.c.get("/timers/add/quick/")
        self.assertEqual(page.status_code, 405)
        page = self.c.post("/timers/add/quick/", follow=True)
        self.assertEqual(page.status_code, 200)

        entry = models.Timer.objects.first()
        page = self.c.get("/timers/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/timers/{}/edit/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/timers/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

        page = self.c.get("/timers/{}/stop/".format(entry.id))
        self.assertEqual(page.status_code, 405)
        page = self.c.post("/timers/{}/stop/".format(entry.id), follow=True)
        self.assertEqual(page.status_code, 200)

        page = self.c.get("/timers/{}/restart/".format(entry.id))
        self.assertEqual(page.status_code, 405)
        page = self.c.post("/timers/{}/restart/".format(entry.id), follow=True)
        self.assertEqual(page.status_code, 200)

        page = self.c.get("/timers/delete-inactive/", follow=True)
        self.assertEqual(page.status_code, 200)
        messages = list(page.context["messages"])
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "No inactive timers exist.")

        entry = models.Timer.objects.first()
        entry.stop()
        page = self.c.get("/timers/delete-inactive/")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["timer_count"], 1)

    def test_timeline_views(self):
        child = models.Child.objects.first()
        response = self.c.get("/timeline/")
        self.assertRedirects(response, "/children/{}/".format(child.slug))

        models.Child.objects.create(
            first_name="Second", last_name="Child", birth_date="2000-01-01"
        )
        response = self.c.get("/timeline/")
        self.assertEqual(response.status_code, 200)

    def test_tummytime_views(self):
        page = self.c.get("/tummy-time/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/tummy-time/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.TummyTime.objects.first()
        page = self.c.get("/tummy-time/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/tummy-time/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)

    def test_weight_views(self):
        page = self.c.get("/weight/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/weight/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Weight.objects.first()
        page = self.c.get("/weight/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/weight/{}/delete/".format(entry.id))
        self.assertEqual(page.status_code, 200)
