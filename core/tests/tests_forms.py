# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.test import Client as HttpClient
from django.utils import timezone
from django.utils.formats import get_format, reset_format_cache

from faker import Faker

from core import models


class FormsTestCaseBase(TestCase):
    c = None
    child = None
    user = None

    @classmethod
    def setUpClass(cls):
        super(FormsTestCaseBase, cls).setUpClass()
        fake = Faker()
        call_command("migrate", verbosity=0)

        cls.c = HttpClient()

        fake_user = fake.simple_profile()
        credentials = {"username": fake_user["username"], "password": fake.password()}
        cls.user = get_user_model().objects.create_user(
            is_superuser=True, **credentials
        )
        cls.c.login(**credentials)

        cls.child = models.Child.objects.create(
            first_name="Child", last_name="One", birth_date=timezone.localdate()
        )

    @staticmethod
    def localdate_string(datetime=None):
        """Converts an object to a local date string for form input."""
        reset_format_cache()
        date_format = get_format("DATE_INPUT_FORMATS")[0]
        return timezone.localdate(datetime).strftime(date_format)

    @staticmethod
    def localtime_string(datetime=None):
        """Converts an object to a local time string for form input."""
        reset_format_cache()
        datetime_format = get_format("DATETIME_INPUT_FORMATS")[0]
        return timezone.localtime(datetime).strftime(datetime_format)


class InitialValuesTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(InitialValuesTestCase, cls).setUpClass()
        cls.timer = models.Timer.objects.create(
            user=cls.user, start=timezone.localtime() - timezone.timedelta(minutes=30)
        )

    def test_child_with_one_child(self):
        page = self.c.get("/sleep/add/")
        self.assertEqual(page.context["form"].initial["child"], self.child)

    def test_child_with_parameter(self):
        child_two = models.Child.objects.create(
            first_name="Child", last_name="Two", birth_date=timezone.localdate()
        )

        page = self.c.get("/sleep/add/")
        self.assertTrue("child" not in page.context["form"].initial)

        page = self.c.get("/sleep/add/?child={}".format(self.child.slug))
        self.assertEqual(page.context["form"].initial["child"], self.child)

        page = self.c.get("/sleep/add/?child={}".format(child_two.slug))
        self.assertEqual(page.context["form"].initial["child"], child_two)

    def test_feeding_type(self):
        child_two = models.Child.objects.create(
            first_name="Child", last_name="Two", birth_date=timezone.localdate()
        )
        child_three = models.Child.objects.create(
            first_name="Child", last_name="Three", birth_date=timezone.localdate()
        )
        start_time = timezone.localtime() - timezone.timedelta(hours=4)
        end_time = timezone.localtime() - timezone.timedelta(hours=3, minutes=30)
        f_one = models.Feeding.objects.create(
            child=self.child,
            start=start_time,
            end=end_time,
            type="breast milk",
            method="left breast",
        )
        f_two = models.Feeding.objects.create(
            child=child_two,
            start=start_time,
            end=end_time,
            type="formula",
            method="bottle",
        )
        f_three = models.Feeding.objects.create(
            child=child_three,
            start=start_time,
            end=end_time,
            type="fortified breast milk",
            method="bottle",
        )

        page = self.c.get("/feedings/add/")
        self.assertTrue("type" not in page.context["form"].initial)

        page = self.c.get("/feedings/add/?child={}".format(self.child.slug))
        self.assertEqual(page.context["form"].initial["type"], f_one.type)
        self.assertFalse("method" in page.context["form"].initial)

        page = self.c.get("/feedings/add/?child={}".format(child_two.slug))
        self.assertEqual(page.context["form"].initial["type"], f_two.type)
        self.assertEqual(page.context["form"].initial["method"], f_two.method)

        page = self.c.get("/feedings/add/?child={}".format(child_three.slug))
        self.assertEqual(page.context["form"].initial["type"], f_three.type)
        self.assertEqual(page.context["form"].initial["method"], f_three.method)

    def test_start_end_set_from_timer(self):
        page = self.c.get("/sleep/add/?timer={}".format(self.timer.id))
        self.assertTrue("start" in page.context["form"].initial)
        self.assertTrue("end" in page.context["form"].initial)

    def test_start_end_not_set_from_invalid_timer(self):
        page = self.c.get("/sleep/add/?timer={}".format(42))
        self.assertTrue("start" not in page.context["form"].initial)
        self.assertTrue("end" not in page.context["form"].initial)


class BMIFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(BMIFormsTestCase, cls).setUpClass()
        cls.bmi = models.BMI.objects.create(
            child=cls.child,
            bmi=30,
            date=timezone.localdate() - timezone.timedelta(days=2),
        )

    def test_add(self):
        params = {
            "child": self.child.id,
            "bmi": 35,
            "date": self.localdate_string(),
        }

        page = self.c.post("/bmi/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Bmi entry for {} added".format(str(self.child)))

    def test_edit(self):
        params = {
            "child": self.bmi.child.id,
            "bmi": self.bmi.bmi + 1,
            "date": self.bmi.date,
        }
        page = self.c.post("/bmi/{}/".format(self.bmi.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.bmi.refresh_from_db()
        self.assertEqual(self.bmi.bmi, params["bmi"])
        self.assertContains(
            page, "Bmi entry for {} updated".format(str(self.bmi.child))
        )

    def test_delete(self):
        page = self.c.post("/bmi/{}/delete/".format(self.bmi.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Bmi entry deleted")


class ChildFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(ChildFormsTestCase, cls).setUpClass()
        cls.child = models.Child.objects.first()

    def test_add(self):
        params = {
            "first_name": "Child",
            "last_name": "Two",
            "birth_date": timezone.localdate(),
        }
        page = self.c.post("/children/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Child entry added")

    def test_edit(self):
        params = {
            "first_name": "Name",
            "last_name": "Changed",
            "birth_date": self.child.birth_date,
        }
        page = self.c.post(
            "/children/{}/edit/".format(self.child.slug), params, follow=True
        )
        self.assertEqual(page.status_code, 200)
        self.child.refresh_from_db()
        self.assertEqual(self.child.last_name, params["last_name"])
        self.assertContains(page, "Child entry updated")

    def test_delete(self):
        params = {"confirm_name": "Incorrect"}
        page = self.c.post(
            "/children/{}/delete/".format(self.child.slug), params, follow=True
        )
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page.context["form"], "confirm_name", "Name does not match child name."
        )

        params["confirm_name"] = str(self.child)
        page = self.c.post(
            "/children/{}/delete/".format(self.child.slug), params, follow=True
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Child entry deleted")


class DiaperChangeFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(DiaperChangeFormsTestCase, cls).setUpClass()
        cls.change = models.DiaperChange.objects.create(
            child=cls.child,
            time=timezone.localtime(),
            wet=True,
            solid=True,
            color="black",
            amount=0.45,
        )

    def test_add(self):
        child = models.Child.objects.first()
        params = {
            "child": child.id,
            "time": self.localtime_string(),
            "color": "black",
            "amount": 0.45,
        }
        page = self.c.post("/changes/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Diaper Change entry for {} added".format(str(child)))

    def test_edit(self):
        params = {
            "child": self.change.child.id,
            "time": self.localtime_string(),
            "wet": self.change.wet,
            "solid": self.change.solid,
            "color": self.change.color,
            "amount": 1.23,
        }
        page = self.c.post("/changes/{}/".format(self.change.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.change.refresh_from_db()
        self.assertEqual(self.change.amount, params["amount"])
        self.assertContains(
            page, "Diaper Change entry for {} updated".format(str(self.change.child))
        )

    def test_delete(self):
        page = self.c.post("/changes/{}/delete/".format(self.change.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Diaper Change entry deleted")


class FeedingFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(FeedingFormsTestCase, cls).setUpClass()
        cls.feeding = models.Feeding.objects.create(
            child=cls.child,
            start=timezone.localtime() - timezone.timedelta(hours=2),
            end=timezone.localtime() - timezone.timedelta(hours=1, minutes=30),
            type="breast milk",
            method="left breast",
            amount=2.5,
        )

    def test_add(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=30)
        params = {
            "child": self.child.id,
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
            "type": "formula",
            "method": "bottle",
            "amount": 0,
        }
        page = self.c.post("/feedings/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Feeding entry for {} added".format(str(self.child)))

    def test_edit(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=30)
        params = {
            "child": self.feeding.child.id,
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
            "type": self.feeding.type,
            "method": self.feeding.method,
            "amount": 100,
        }
        page = self.c.post("/feedings/{}/".format(self.feeding.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.feeding.refresh_from_db()
        self.assertEqual(self.feeding.amount, params["amount"])
        self.assertContains(
            page, "Feeding entry for {} updated".format(str(self.feeding.child))
        )

    def test_delete(self):
        page = self.c.post("/feedings/{}/delete/".format(self.feeding.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Feeding entry deleted")


class HeadCircumferenceFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(HeadCircumferenceFormsTestCase, cls).setUpClass()
        cls.head_circumference = models.HeadCircumference.objects.create(
            child=cls.child,
            head_circumference=15,
            date=timezone.localdate() - timezone.timedelta(days=2),
        )

    def test_add(self):
        params = {
            "child": self.child.id,
            "head_circumference": 20,
            "date": self.localdate_string(),
        }

        page = self.c.post("/head-circumference/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page, "Head Circumference entry for {} added".format(str(self.child))
        )

    def test_edit(self):
        params = {
            "child": self.head_circumference.child.id,
            "head_circumference": self.head_circumference.head_circumference + 1,
            "date": self.head_circumference.date,
        }
        page = self.c.post(
            "/head-circumference/{}/".format(self.head_circumference.id),
            params,
            follow=True,
        )
        self.assertEqual(page.status_code, 200)
        self.head_circumference.refresh_from_db()
        self.assertEqual(
            self.head_circumference.head_circumference, params["head_circumference"]
        )
        self.assertContains(
            page,
            "Head Circumference entry for {} updated".format(
                str(self.head_circumference.child)
            ),
        )

    def test_delete(self):
        page = self.c.post(
            "/head-circumference/{}/delete/".format(self.head_circumference.id),
            follow=True,
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Head Circumference entry deleted")


class HeightFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(HeightFormsTestCase, cls).setUpClass()
        cls.height = models.Height.objects.create(
            child=cls.child,
            height=12.5,
            date=timezone.localdate() - timezone.timedelta(days=2),
        )

    def test_add(self):
        params = {
            "child": self.child.id,
            "height": 13.5,
            "date": self.localdate_string(),
        }

        page = self.c.post("/height/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Height entry for {} added".format(str(self.child)))

    def test_edit(self):
        params = {
            "child": self.height.child.id,
            "height": self.height.height + 1,
            "date": self.height.date,
        }
        page = self.c.post("/height/{}/".format(self.height.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.height.refresh_from_db()
        self.assertEqual(self.height.height, params["height"])
        self.assertContains(
            page, "Height entry for {} updated".format(str(self.height.child))
        )

    def test_delete(self):
        page = self.c.post("/height/{}/delete/".format(self.height.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Height entry deleted")


class NoteFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(NoteFormsTestCase, cls).setUpClass()
        cls.note = models.Note.objects.create(
            child=cls.child,
            note="Test note!",
            time=timezone.localtime() - timezone.timedelta(days=2),
        )

    def test_add(self):
        params = {
            "child": self.child.id,
            "note": "New note",
            "time": self.localtime_string(),
        }

        page = self.c.post("/notes/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Note entry for {} added".format(str(self.child)))

    def test_edit(self):
        params = {
            "child": self.note.child.id,
            "note": "changed note",
            "time": self.note.time,
        }
        page = self.c.post("/notes/{}/".format(self.note.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.note.refresh_from_db()
        self.assertEqual(self.note.note, params["note"])
        self.assertContains(
            page, "Note entry for {} updated".format(str(self.note.child))
        )

    def test_delete(self):
        page = self.c.post("/notes/{}/delete/".format(self.note.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Note entry deleted")


class PumpingFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(PumpingFormsTestCase, cls).setUpClass()
        start = timezone.localtime() - timezone.timedelta(days=1)
        end = start + timezone.timedelta(minutes=3)
        cls.bp = models.Pumping.objects.create(
            child=cls.child,
            amount=50.0,
            start=start,
            end=end,
        )

    def test_add(self):
        start = timezone.localtime() - timezone.timedelta(days=3)
        end = start + timezone.timedelta(minutes=5)
        params = {
            "child": self.child.id,
            "amount": "50.0",
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
        }

        page = self.c.post("/pumping/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Pumping entry for {} added".format(str(self.child)))

    def test_edit(self):
        params = {
            "child": self.bp.child.id,
            "amount": self.bp.amount + 2,
            "start": self.localtime_string(self.bp.start),
            "end": self.localtime_string(self.bp.end + timezone.timedelta(minutes=15)),
        }
        page = self.c.post("/pumping/{}/".format(self.bp.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.bp.refresh_from_db()
        self.assertEqual(self.bp.amount, params["amount"])
        self.assertContains(
            page, "Pumping entry for {} updated".format(str(self.bp.child))
        )

    def test_delete(self):
        page = self.c.post("/pumping/{}/delete/".format(self.bp.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Pumping entry deleted")


class SleepFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(SleepFormsTestCase, cls).setUpClass()
        cls.sleep = models.Sleep.objects.create(
            child=cls.child,
            start=timezone.localtime() - timezone.timedelta(hours=6),
            end=timezone.localtime() - timezone.timedelta(hours=4),
        )

    def test_add(self):
        # Prevent potential sleep entry intersection errors.
        models.Sleep.objects.all().delete()

        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=2)
        params = {
            "child": self.child.id,
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
        }

        page = self.c.post("/sleep/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Sleep entry for {} added".format(str(self.child)))

    def test_edit(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=2)
        params = {
            "child": self.sleep.child.id,
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
        }
        page = self.c.post("/sleep/{}/".format(self.sleep.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.sleep.refresh_from_db()
        self.assertEqual(self.localtime_string(self.sleep.end), params["end"])
        self.assertContains(
            page, "Sleep entry for {} updated".format(str(self.sleep.child))
        )

    def test_delete(self):
        page = self.c.post("/sleep/{}/delete/".format(self.sleep.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Sleep entry deleted")

    def test_nap_default(self):
        models.Sleep.settings.nap_start_min = datetime.time(0, 0, 0)
        models.Sleep.settings.nap_start_max = datetime.time(23, 59, 59)
        response = self.c.get("/sleep/add/")
        self.assertTrue(response.context["form"].initial["nap"])

    def test_not_nap_default(self):
        models.Sleep.settings.nap_start_min = datetime.time(0, 0, 0)
        models.Sleep.settings.nap_start_max = datetime.time(0, 0, 0)
        response = self.c.get("/sleep/add/")
        self.assertFalse(response.context["form"].initial["nap"])


class TaggedFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TaggedFormsTestCase, cls).setUpClass()

        cls.note = models.Note.objects.create(
            child=cls.child,
            note="Setup note",
            time=timezone.now() - timezone.timedelta(days=2),
        )
        cls.note.tags.add("oldtag")
        cls.oldtag = models.Tag.objects.filter(slug="oldtag").first()

    def test_add_no_tags(self):
        params = {
            "child": self.child.id,
            "note": "note with no tags",
            "time": (timezone.now() - timezone.timedelta(minutes=1)).isoformat(),
        }

        page = self.c.post("/notes/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "note with no tags")

    def test_add_with_tags(self):
        params = {
            "child": self.child.id,
            "note": "this note has tags",
            "time": (timezone.now() - timezone.timedelta(minutes=1)).isoformat(),
            "tags": 'A,B,"setup tag"',
        }

        old_notes = list(models.Note.objects.all())

        page = self.c.post("/notes/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "this note has tags")

        new_notes = list(models.Note.objects.all())

        # Find the new tag and extract its tags
        old_pks = [n.pk for n in old_notes]
        new_note = [n for n in new_notes if n.pk not in old_pks][0]
        new_note_tag_names = [t.name for t in new_note.tags.all()]

        self.assertSetEqual(set(new_note_tag_names), {"A", "B", "setup tag"})

    def test_edit(self):
        old_tag_last_used = self.oldtag.last_used

        params = {
            "child": self.note.child.id,
            "note": "Edited note",
            "time": self.localdate_string(),
            "tags": "oldtag,newtag",
        }
        page = self.c.post("/notes/{}/".format(self.note.id), params, follow=True)
        self.assertEqual(page.status_code, 200)

        self.note.refresh_from_db()
        self.oldtag.refresh_from_db()
        self.assertEqual(self.note.note, params["note"])
        self.assertContains(
            page, "Note entry for {} updated".format(str(self.note.child))
        )

        self.assertSetEqual(
            set(t.name for t in self.note.tags.all()), {"oldtag", "newtag"}
        )

        # Old tag remains old, because it was not added
        self.assertEqual(old_tag_last_used, self.oldtag.last_used)

        # Second phase: Remove all tags then add "oldtag" through posting
        # which should update the last_used tag
        self.note.tags.clear()
        self.note.save()

        params = {
            "child": self.note.child.id,
            "note": "Edited note (2)",
            "time": self.localdate_string(),
            "tags": "oldtag",
        }
        page = self.c.post("/notes/{}/".format(self.note.id), params, follow=True)
        self.assertEqual(page.status_code, 200)

        self.note.refresh_from_db()
        self.oldtag.refresh_from_db()

        self.assertLess(old_tag_last_used, self.oldtag.last_used)

    def test_delete(self):
        page = self.c.post("/notes/{}/delete/".format(self.note.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Note entry deleted")


class TemperatureFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TemperatureFormsTestCase, cls).setUpClass()
        cls.temp = models.Temperature.objects.create(
            child=cls.child,
            temperature=98.6,
            time=timezone.localtime() - timezone.timedelta(days=1),
        )

    def test_add(self):
        params = {
            "child": self.child.id,
            "temperature": "98.6",
            "time": self.localtime_string(),
        }

        page = self.c.post("/temperature/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page, "Temperature entry for {} added".format(str(self.child))
        )

    def test_edit(self):
        params = {
            "child": self.temp.child.id,
            "temperature": self.temp.temperature + 2,
            "time": self.localtime_string(),
        }
        page = self.c.post("/temperature/{}/".format(self.temp.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.temp.refresh_from_db()
        self.assertEqual(self.temp.temperature, params["temperature"])
        self.assertContains(
            page, "Temperature entry for {} updated".format(str(self.temp.child))
        )

    def test_delete(self):
        page = self.c.post("/temperature/{}/delete/".format(self.temp.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Temperature entry deleted")


class TummyTimeFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TummyTimeFormsTestCase, cls).setUpClass()
        cls.tt = models.TummyTime.objects.create(
            child=cls.child,
            start=timezone.localtime() - timezone.timedelta(hours=2),
            end=timezone.localtime() - timezone.timedelta(hours=1, minutes=50),
        )

    def test_add(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=2)
        params = {
            "child": self.child.id,
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
            "milestone": "",
        }

        page = self.c.post("/tummy-time/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(
            page, "Tummy Time entry for {} added".format(str(self.child))
        )

    def test_edit(self):
        end = timezone.localtime()
        start = end - timezone.timedelta(minutes=1, seconds=32)
        params = {
            "child": self.tt.child.id,
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
            "milestone": "Moved head!",
        }
        page = self.c.post("/tummy-time/{}/".format(self.tt.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.tt.refresh_from_db()
        self.assertEqual(self.tt.milestone, params["milestone"])
        self.assertContains(
            page, "Tummy Time entry for {} updated".format(str(self.tt.child))
        )

    def test_delete(self):
        page = self.c.post("/tummy-time/{}/delete/".format(self.tt.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Tummy Time entry deleted")


class TimerFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(TimerFormsTestCase, cls).setUpClass()
        cls.timer = models.Timer.objects.create(user=cls.user)

    def test_add(self):
        params = {
            "child": self.child.id,
            "name": "Test Timer",
            "start": self.localtime_string(),
        }
        page = self.c.post("/timers/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, params["name"])
        self.assertContains(page, params["child"])

    def test_edit(self):
        start_time = self.timer.start - timezone.timedelta(hours=1)
        params = {"name": "New Timer Name", "start": self.localtime_string(start_time)}
        page = self.c.post(
            "/timers/{}/edit/".format(self.timer.id), params, follow=True
        )
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, params["name"])
        self.timer.refresh_from_db()
        self.assertEqual(self.localtime_string(self.timer.start), params["start"])


class ValidationsTestCase(FormsTestCaseBase):
    def test_validate_date(self):
        future = timezone.localtime() + timezone.timedelta(days=10)
        params = {
            "child": self.child,
            "weight": "8.5",
            "date": self.localdate_string(future),
        }
        entry = models.Weight.objects.create(**params)

        page = self.c.post("/weight/{}/".format(entry.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page.context["form"], "date", "Date can not be in the future."
        )

    def test_validate_duration(self):
        end = timezone.localtime() - timezone.timedelta(minutes=10)
        start = end + timezone.timedelta(minutes=5)
        params = {
            "child": self.child,
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
            "milestone": "",
        }

        page = self.c.post("/tummy-time/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page.context["form"], None, "Start time must come before end time."
        )

        start = end - timezone.timedelta(weeks=53)
        params["start"] = self.localtime_string(start)
        page = self.c.post("/tummy-time/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(page.context["form"], None, "Duration too long.")

    def test_validate_time(self):
        future = timezone.localtime() + timezone.timedelta(hours=1)
        params = {
            "child": self.child,
            "start": self.localtime_string(),
            "end": self.localtime_string(future),
            "milestone": "",
        }

        page = self.c.post("/tummy-time/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page.context["form"], "end", "Date/time can not be in the future."
        )

    def test_validate_unique_period(self):
        entry = models.TummyTime.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=10),
            end=timezone.localtime() - timezone.timedelta(minutes=5),
        )

        start = entry.start - timezone.timedelta(minutes=2)
        end = entry.end + timezone.timedelta(minutes=2)
        params = {
            "child": entry.child.id,
            "start": self.localtime_string(start),
            "end": self.localtime_string(end),
            "milestone": "",
        }

        page = self.c.post("/tummy-time/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertFormError(
            page.context["form"],
            None,
            "Another entry intersects the specified time period.",
        )


class WeightFormsTestCase(FormsTestCaseBase):
    @classmethod
    def setUpClass(cls):
        super(WeightFormsTestCase, cls).setUpClass()
        cls.weight = models.Weight.objects.create(
            child=cls.child,
            weight=8,
            date=timezone.localdate() - timezone.timedelta(days=2),
        )

    def test_add(self):
        params = {
            "child": self.child.id,
            "weight": 8.5,
            "date": self.localdate_string(),
        }

        page = self.c.post("/weight/add/", params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Weight entry for {} added".format(str(self.child)))

    def test_edit(self):
        params = {
            "child": self.weight.child.id,
            "weight": self.weight.weight + 1,
            "date": self.localdate_string(),
        }
        page = self.c.post("/weight/{}/".format(self.weight.id), params, follow=True)
        self.assertEqual(page.status_code, 200)
        self.weight.refresh_from_db()
        self.assertEqual(self.weight.weight, params["weight"])
        self.assertContains(
            page, "Weight entry for {} updated".format(str(self.weight.child))
        )

    def test_delete(self):
        page = self.c.post("/weight/{}/delete/".format(self.weight.id), follow=True)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "Weight entry deleted")
