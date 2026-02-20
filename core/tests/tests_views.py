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

    def test_tags_views(self):
        page = self.c.get("/tags/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/tags/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Tag.objects.first()
        page = self.c.get("/tags/{}/".format(entry.slug))
        self.assertEqual(page.status_code, 200)
        entry = models.Tag.objects.first()
        page = self.c.get("/tags/{}/edit".format(entry.slug))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/tags/{}/delete/".format(entry.slug))
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

        page = self.c.get("/timers/{}/restart/".format(entry.id))
        self.assertEqual(page.status_code, 405)
        page = self.c.post("/timers/{}/restart/".format(entry.id), follow=True)
        self.assertEqual(page.status_code, 200)

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

    def test_medication_views(self):
        page = self.c.get("/medications/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/medications/add/")
        self.assertEqual(page.status_code, 200)

        child = models.Child.objects.first()
        med = models.Medication.objects.create(
            child=child,
            name="Vitamin D",
            time=timezone.localtime(),
        )
        page = self.c.get("/medications/{}/".format(med.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/medications/{}/delete/".format(med.id))
        self.assertEqual(page.status_code, 200)

    def test_medicationschedule_views(self):
        page = self.c.get("/medication-schedules/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/medication-schedules/add/")
        self.assertEqual(page.status_code, 200)

        child = models.Child.objects.first()
        schedule = models.MedicationSchedule.objects.create(
            child=child,
            name="Vitamin D",
            frequency="daily",
        )
        page = self.c.get("/medication-schedules/{}/".format(schedule.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/medication-schedules/{}/delete/".format(schedule.id))
        self.assertEqual(page.status_code, 200)

    def test_medication_give_view(self):
        child = models.Child.objects.first()
        schedule = models.MedicationSchedule.objects.create(
            child=child,
            name="Ibuprofen",
            amount=100,
            amount_unit="mg",
            frequency="daily",
        )
        # GET should not be allowed
        page = self.c.get("/medication-schedules/{}/give/".format(schedule.id))
        self.assertEqual(page.status_code, 405)
        # POST should create a Medication and redirect
        page = self.c.post(
            "/medication-schedules/{}/give/".format(schedule.id), follow=True
        )
        self.assertEqual(page.status_code, 200)
        med = models.Medication.objects.filter(medication_schedule=schedule).first()
        self.assertIsNotNone(med)
        self.assertEqual(med.name, "Ibuprofen")
        self.assertEqual(med.amount, 100)

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


class LastEntryBannerTestCase(TestCase):
    """Test that add forms include last_entry context when child is known."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fake = Faker()
        call_command("migrate", verbosity=0)

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

        cls.child = models.Child.objects.create(
            first_name="Test",
            last_name="Baby",
            birth_date=timezone.localdate(),
        )

    def test_feeding_add_shows_last_entry(self):
        models.Feeding.objects.create(
            child=self.child,
            start=timezone.now() - timezone.timedelta(hours=2),
            end=timezone.now() - timezone.timedelta(hours=1),
            type="breast milk",
            method="left breast",
        )
        page = self.c.get("/feedings/add/", {"child": self.child.slug})
        self.assertEqual(page.status_code, 200)
        self.assertIn("last_entry", page.context)
        self.assertIsInstance(page.context["last_entry"], models.Feeding)
        self.assertContains(page, "Last")

    def test_sleep_add_shows_last_entry(self):
        models.Sleep.objects.create(
            child=self.child,
            start=timezone.now() - timezone.timedelta(hours=3),
            end=timezone.now() - timezone.timedelta(hours=1),
        )
        page = self.c.get("/sleep/add/", {"child": self.child.slug})
        self.assertEqual(page.status_code, 200)
        self.assertIn("last_entry", page.context)
        self.assertIsInstance(page.context["last_entry"], models.Sleep)

    def test_diaperchange_add_shows_last_entry(self):
        models.DiaperChange.objects.create(
            child=self.child,
            time=timezone.now() - timezone.timedelta(hours=1),
            wet=True,
            solid=False,
        )
        page = self.c.get("/changes/add/", {"child": self.child.slug})
        self.assertEqual(page.status_code, 200)
        self.assertIn("last_entry", page.context)
        self.assertContains(page, "Wet")

    def test_temperature_add_shows_last_entry(self):
        models.Temperature.objects.create(
            child=self.child,
            time=timezone.now() - timezone.timedelta(hours=1),
            temperature=37.5,
        )
        page = self.c.get("/temperature/add/", {"child": self.child.slug})
        self.assertEqual(page.status_code, 200)
        self.assertIn("last_entry", page.context)
        self.assertContains(page, "37.5")

    def test_no_last_entry_without_child_param(self):
        """Without a child query param (and multiple children), no banner."""
        models.Child.objects.create(
            first_name="Second",
            last_name="Child",
            birth_date=timezone.localdate(),
        )
        page = self.c.get("/feedings/add/")
        self.assertEqual(page.status_code, 200)
        self.assertNotIn("last_entry", page.context)
        models.Child.objects.filter(first_name="Second").delete()

    def test_no_last_entry_when_none_exist(self):
        """With child param but no prior entries, no banner."""
        page = self.c.get("/pumping/add/", {"child": self.child.slug})
        self.assertEqual(page.status_code, 200)
        self.assertNotIn("last_entry", page.context)

    def test_child_add_has_no_last_entry(self):
        """Child model has no child FK, so no banner."""
        page = self.c.get("/children/add/")
        self.assertEqual(page.status_code, 200)
        self.assertNotIn("last_entry", page.context)

    def test_single_child_auto_resolves(self):
        """When only one child in DB, last_entry is shown without query param."""
        other_children = models.Child.objects.exclude(pk=self.child.pk)
        other_children.delete()
        models.Feeding.objects.create(
            child=self.child,
            start=timezone.now() - timezone.timedelta(hours=2),
            end=timezone.now() - timezone.timedelta(hours=1),
            type="breast milk",
            method="left breast",
        )
        page = self.c.get("/feedings/add/")
        self.assertEqual(page.status_code, 200)
        self.assertIn("last_entry", page.context)

    def test_summary_includes_duration(self):
        models.Sleep.objects.create(
            child=self.child,
            start=timezone.now() - timezone.timedelta(hours=3),
            end=timezone.now() - timezone.timedelta(hours=1),
        )
        page = self.c.get("/sleep/add/", {"child": self.child.slug})
        summary = page.context.get("last_entry_summary", "")
        self.assertIn("2", summary)


class LastEntryBannerFragmentTestCase(TestCase):
    """Test the HTML fragment endpoint for the last-entry banner."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        fake = Faker()
        call_command("migrate", verbosity=0)

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

        cls.child = models.Child.objects.create(
            first_name="Fragment",
            last_name="Baby",
            birth_date=timezone.localdate(),
        )

    def test_fragment_returns_banner_html(self):
        models.Feeding.objects.create(
            child=self.child,
            start=timezone.now() - timezone.timedelta(hours=2),
            end=timezone.now() - timezone.timedelta(hours=1),
            type="breast milk",
            method="left breast",
        )
        url = "/last-entry-banner/feeding/{}/".format(self.child.pk)
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "last-entry-banner")
        self.assertContains(resp, "Last")

    def test_fragment_empty_when_no_entries(self):
        url = "/last-entry-banner/pumping/{}/".format(self.child.pk)
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "alert-info")

    def test_fragment_404_invalid_model(self):
        url = "/last-entry-banner/bogus/{}/".format(self.child.pk)
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 404)

    def test_fragment_404_invalid_child(self):
        url = "/last-entry-banner/feeding/99999/"
        resp = self.c.get(url)
        self.assertEqual(resp.status_code, 404)
