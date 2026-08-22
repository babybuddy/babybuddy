# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core import models


class BMITestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.bmi = models.BMI.objects.create(
            child=self.child,
            date=timezone.localdate(),
            bmi=63.2,
        )

    def test_weight_create(self):
        self.assertEqual(self.bmi, models.BMI.objects.first())
        self.assertEqual(str(self.bmi), "BMI")
        self.assertEqual(self.bmi.bmi, 63.2)


class ChildTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)

    def test_child_create(self):
        child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.assertEqual(child, models.Child.objects.get(first_name="First"))
        self.assertEqual(child.slug, "first-last")
        self.assertEqual(str(child), "First Last")
        self.assertEqual(child.name(), "First Last")
        self.assertEqual(child.name(reverse=True), "Last, First")

    def test_child_create_without_last_name(self):
        child = models.Child.objects.create(
            first_name="Nolastname", birth_date=timezone.localdate()
        )
        self.assertEqual(child, models.Child.objects.get(first_name="Nolastname"))
        self.assertEqual(child.slug, "nolastname")
        self.assertEqual(str(child), "Nolastname")
        self.assertEqual(child.name(), "Nolastname")
        self.assertEqual(child.name(reverse=True), "Nolastname")

    def test_child_count(self):
        self.assertEqual(models.Child.count(), 0)
        models.Child.objects.create(
            first_name="First 1", last_name="Last 1", birth_date=timezone.localdate()
        )
        self.assertEqual(models.Child.count(), 1)
        child = models.Child.objects.create(
            first_name="First 2", last_name="Last 2", birth_date=timezone.localdate()
        )
        self.assertEqual(models.Child.count(), 2)
        child.delete()
        self.assertEqual(models.Child.count(), 1)

    def test_child_birth_datetime(self):
        birth_date = timezone.localdate()
        models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=birth_date
        )
        self.assertEqual(models.Child.objects.last().birth_datetime(), birth_date)
        birth_time = datetime.datetime.now().time()
        models.Child.objects.create(
            first_name="Second",
            last_name="Last",
            birth_date=birth_date,
            birth_time=birth_time,
        )
        self.assertEqual(
            models.Child.objects.last().birth_datetime(),
            timezone.make_aware(datetime.datetime.combine(birth_date, birth_time)),
        )


class DiaperChangeTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.change = models.DiaperChange.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=1),
            wet=1,
            solid=1,
            color="black",
            amount=1.25,
        )

    def test_diaperchange_create(self):
        self.assertEqual(self.change, models.DiaperChange.objects.first())
        self.assertEqual(str(self.change), "Diaper Change")
        self.assertEqual(self.change.child, self.child)
        self.assertTrue(self.change.wet)
        self.assertTrue(self.change.solid)
        self.assertEqual(self.change.color, "black")
        self.assertEqual(self.change.amount, 1.25)

    def test_diaperchange_attributes(self):
        self.assertListEqual(
            self.change.attributes(),
            ["Wet", "Solid Black"],
        )  # color inlined into solid since wet/solid_amount split

    def test_diaperchange_color_choices(self):
        colors = [
            choice[0] for choice in models.DiaperChange._meta.get_field("color").choices
        ]
        # Create a fresh child so the setUp fixture's DiaperChange doesn't
        # interfere with the count.
        child = models.Child.objects.create(
            first_name="Color", last_name="Test", birth_date=timezone.localdate()
        )
        for color in colors:
            models.DiaperChange.objects.create(
                child=child,
                time=timezone.localtime(),
                wet=False,
                solid=False,
                color=color,
            )
        self.assertEqual(
            models.DiaperChange.objects.filter(child=child).count(), len(colors)
        )


class FeedingTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_feeding_create(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="formula",
            method="bottle",
            amount=2,
        )
        self.assertEqual(feeding, models.Feeding.objects.first())
        self.assertEqual(str(feeding), "Feeding")
        self.assertEqual(feeding.duration, feeding.end - feeding.start)

    def test_method_both_breasts(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="breast milk",
            method="both breasts",
        )
        self.assertEqual(feeding, models.Feeding.objects.first())
        self.assertEqual(str(feeding), "Feeding")
        self.assertEqual(feeding.method, "both breasts")

    def test_method_tube(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="breast milk",
            method="tube",
            amount=15,
        )
        self.assertEqual(feeding.method, "tube")
        self.assertEqual(feeding.get_method_display(), "Tube feeding")

    def test_method_cup_feeding(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="breast milk",
            method="cup feeding",
        )
        self.assertEqual(feeding.method, "cup feeding")
        self.assertEqual(feeding.get_method_display(), "Cup feeding")

    def test_method_finger_feeding(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="breast milk",
            method="finger feeding",
        )
        self.assertEqual(feeding.method, "finger feeding")
        self.assertEqual(feeding.get_method_display(), "Finger feeding")

    def test_breastfeeding_modifier_default(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
        )
        self.assertEqual(feeding.breastfeeding_modifier, "none")
        self.assertIsNone(feeding.sns_amount)
        self.assertEqual(feeding.sns_milk_type, "")

    def test_breastfeeding_modifier_nipple_shield(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
            breastfeeding_modifier="nipple_shield",
        )
        self.assertEqual(feeding.breastfeeding_modifier, "nipple_shield")
        self.assertEqual(feeding.get_breastfeeding_modifier_display(), "Nipple shield")

    def test_breastfeeding_modifier_nipple_shield_sns(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="breast milk",
            method="left breast",
            breastfeeding_modifier="nipple_shield_sns",
            sns_amount=20,
            sns_milk_type="formula",
        )
        self.assertEqual(feeding.breastfeeding_modifier, "nipple_shield_sns")
        self.assertEqual(feeding.sns_amount, 20)
        self.assertEqual(feeding.sns_milk_type, "formula")


class HeadCircumferenceTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.hc = models.HeadCircumference.objects.create(
            child=self.child,
            date=timezone.localdate(),
            head_circumference=13.25,
        )

    def test_weight_create(self):
        self.assertEqual(self.hc, models.HeadCircumference.objects.first())
        self.assertEqual(str(self.hc), "Head Circumference")
        self.assertEqual(self.hc.head_circumference, 13.25)


class HeightTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.height = models.Height.objects.create(
            child=self.child,
            date=timezone.localdate(),
            height=34.5,
        )

    def test_weight_create(self):
        self.assertEqual(self.height, models.Height.objects.first())
        self.assertEqual(str(self.height), "Height")
        self.assertEqual(self.height.height, 34.5)


class NoteTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_note_create(self):
        note = models.Note.objects.create(
            child=self.child, note="Note", time=timezone.localtime()
        )
        self.assertEqual(note, models.Note.objects.first())
        self.assertEqual(str(note), "Note")


class PumpingTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        start = timezone.localtime() - timezone.timedelta(days=1)
        end = start + timezone.timedelta(minutes=14)
        self.pumping = models.Pumping.objects.create(
            child=self.child,
            start=start,
            end=end,
            amount=98.6,
        )

    def test_pumping_create(self):
        self.assertEqual(self.pumping, models.Pumping.objects.first())
        self.assertIn("98.6", str(self.pumping))
        self.assertEqual(self.pumping.amount, 98.6)

    def test_pumping_method_default(self):
        self.assertEqual(self.pumping.method, "")

    def test_pumping_method_electric_pump(self):
        pumping = models.Pumping.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=20),
            end=timezone.localtime(),
            amount=50,
            method="electric pump",
        )
        self.assertEqual(pumping.method, "electric pump")
        self.assertEqual(pumping.get_method_display(), "Electric pump")

    def test_pumping_method_hand_expression(self):
        pumping = models.Pumping.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=10),
            end=timezone.localtime(),
            amount=15,
            method="hand expression",
        )
        self.assertEqual(pumping.method, "hand expression")
        self.assertEqual(pumping.get_method_display(), "Hand expression")

    def test_pumping_method_wearable_pump(self):
        pumping = models.Pumping.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=25),
            end=timezone.localtime(),
            amount=40,
            method="wearable pump",
        )
        self.assertEqual(pumping.method, "wearable pump")
        self.assertEqual(pumping.get_method_display(), "Wearable pump")


class SleepTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_sleep_create(self):
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
        )
        self.assertEqual(sleep, models.Sleep.objects.first())
        self.assertEqual(str(sleep), "Sleep")
        self.assertEqual(sleep.duration, sleep.end - sleep.start)

    def test_sleep_nap(self):
        models.Sleep.settings.nap_start_min = datetime.time(0, 0, 0)
        models.Sleep.settings.nap_start_max = datetime.time(23, 59, 59)
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.now(),
            end=(timezone.now() + timezone.timedelta(hours=2)),
        )
        self.assertTrue(sleep.nap)

    def test_sleep_not_nap(self):
        models.Sleep.settings.nap_start_min = datetime.time(0, 0, 0)
        models.Sleep.settings.nap_start_max = datetime.time(0, 0, 0)
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.now(),
            end=(timezone.now() + timezone.timedelta(hours=8)),
        )
        self.assertFalse(sleep.nap)

        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.now(),
            end=(timezone.now() + timezone.timedelta(hours=8)),
            nap=True,
        )
        self.assertTrue(sleep.nap)


class TagTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_create_tag(self):
        tag1 = models.Tag.objects.create(name="Tag 1")
        self.assertEqual(tag1, models.Tag.objects.first())

        tag2 = models.Tag.objects.create(name="Tag 2")
        self.assertEqual(tag2, models.Tag.objects.filter(name="Tag 2").get())

    def test_tag_complementary_color(self):
        light_tag = models.Tag.objects.create(name="Light Tag", color="#ffffff")
        self.assertEqual(light_tag.complementary_color, models.Tag.DARK_COLOR)

        dark_tag = models.Tag.objects.create(name="Dark Tag", color="#000000")
        self.assertEqual(dark_tag.complementary_color, models.Tag.LIGHT_COLOR)

    def test_model_tagging(self):
        temp = models.Temperature.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=1),
            temperature=98.6,
        )
        temp.tags.add("Tag 1")
        self.assertEqual(
            temp.tags.all().get(), models.Tag.objects.filter(name="Tag 1").get()
        )


class TemperatureTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.temp = models.Temperature.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=1),
            temperature=98.6,
        )

    def test_temperature_create(self):
        self.assertEqual(self.temp, models.Temperature.objects.first())
        self.assertEqual(str(self.temp), "Temperature")
        self.assertEqual(self.temp.temperature, 98.6)


class TimerTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.user = get_user_model().objects.first()
        self.named = models.Timer.objects.create(
            name="Named", user=self.user, child=child
        )
        self.unnamed = models.Timer.objects.create(user=self.user)

    def test_timer_create(self):
        self.assertEqual(self.named, models.Timer.objects.get(name="Named"))
        self.assertEqual(str(self.named), "Named")
        self.assertEqual(self.unnamed, models.Timer.objects.get(name=None))
        self.assertEqual(str(self.unnamed), "Timer #{}".format(self.unnamed.id))

    def test_timer_title_with_child(self):
        self.assertEqual(self.named.title_with_child, str(self.named))

        models.Child.objects.create(
            first_name="Child", last_name="Two", birth_date=timezone.localdate()
        )
        self.assertEqual(
            self.named.title_with_child,
            "{} ({})".format(str(self.named), str(self.named.child)),
        )

    def test_timer_user_username(self):
        self.assertEqual(self.named.user_username, self.user.get_username())
        self.user.first_name = "User"
        self.user.last_name = "Name"
        self.user.save()
        self.assertEqual(self.named.user_username, self.user.get_full_name())

    def test_timer_restart(self):
        self.named.restart()
        self.assertGreaterEqual(timezone.localtime(), self.named.start)

    def test_timer_duration(self):
        timer = models.Timer.objects.create(user=get_user_model().objects.first())
        timer.start = timezone.localtime() - timezone.timedelta(minutes=30)
        timer.save()
        timer.refresh_from_db()

        self.assertEqual(
            timer.duration().seconds, timezone.timedelta(minutes=30).seconds
        )


class TummyTimeTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_tummytime_create(self):
        tummy_time = models.TummyTime.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
        )
        self.assertEqual(tummy_time, models.TummyTime.objects.first())
        self.assertEqual(str(tummy_time), "Tummy Time")
        self.assertEqual(tummy_time.duration, tummy_time.end - tummy_time.start)


class WeightTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.weight = models.Weight.objects.create(
            child=self.child,
            date=timezone.localdate(),
            weight=23,
        )

    def test_weight_create(self):
        self.assertEqual(self.weight, models.Weight.objects.first())
        self.assertEqual(str(self.weight), "Weight")
        self.assertEqual(self.weight.weight, 23)


class MedicationTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.medication = models.Medication.objects.create(
            child=self.child,
            name="Tylenol",
            dosage=5.0,
            dosage_unit="ml",
            time=timezone.localtime() - timezone.timedelta(hours=1),
            next_dose_interval=timezone.timedelta(hours=4),
        )

    def test_medication_create(self):
        self.assertEqual(self.medication, models.Medication.objects.first())
        self.assertEqual(str(self.medication), "Medication")
        self.assertEqual(self.medication.name, "Tylenol")
        self.assertEqual(self.medication.dosage, 5.0)
        self.assertEqual(self.medication.dosage_unit, "ml")

    def test_medication_with_interval(self):
        self.assertEqual(
            self.medication.next_dose_interval, timezone.timedelta(hours=4)
        )

    def test_medication_without_dosage(self):
        # Dosage is optional
        medication = models.Medication.objects.create(
            child=self.child,
            name="Vitamin D",
            time=timezone.localtime(),
        )
        self.assertIsNone(medication.dosage)
        self.assertEqual(medication.dosage_unit, "")

    def test_medication_with_tags(self):
        self.medication.tags.add("fever", "morning")
        self.assertEqual(self.medication.tags.count(), 2)
        self.assertTrue(self.medication.tags.filter(name="fever").exists())

    def test_medication_validation_future_time(self):
        from django.core.exceptions import ValidationError

        future_time = timezone.localtime() + timezone.timedelta(hours=1)
        medication = models.Medication(
            child=self.child,
            name="Future Medication",
            dosage=5.0,
            dosage_unit="ml",
            time=future_time,
        )
        with self.assertRaises(ValidationError):
            medication.full_clean()


class PumpingInventoryWiringTestCase(TestCase):
    """FR-5: Pumping session auto-creates a FeedInventory entry on save."""

    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_pumping_creates_feed_inventory(self):
        """Creating a Pumping record auto-creates a linked FeedInventory."""
        start = timezone.localtime() - timezone.timedelta(minutes=20)
        end = timezone.localtime() - timezone.timedelta(minutes=5)
        pumping = models.Pumping.objects.create(
            child=self.child,
            start=start,
            end=end,
            amount=100.0,
        )
        fi = models.FeedInventory.objects.filter(pumping_session=pumping)
        self.assertTrue(fi.exists(), "FeedInventory was not auto-created")
        entry = fi.first()
        self.assertEqual(entry.child, self.child)
        self.assertEqual(entry.type, "breast_milk")
        self.assertEqual(entry.amount, 100.0)
        self.assertEqual(entry.amount_unit, "ml")
        self.assertEqual(entry.amount_remaining, 100.0)

    def test_pumping_update_does_not_duplicate_feed_inventory(self):
        """Updating a Pumping record should NOT create a second FeedInventory."""
        start = timezone.localtime() - timezone.timedelta(minutes=30)
        end = timezone.localtime() - timezone.timedelta(minutes=15)
        pumping = models.Pumping.objects.create(
            child=self.child,
            start=start,
            end=end,
            amount=50.0,
        )
        self.assertEqual(
            models.FeedInventory.objects.filter(pumping_session=pumping).count(), 1
        )
        # Now update the pumping record
        pumping.amount = 60.0
        pumping.save()
        self.assertEqual(
            models.FeedInventory.objects.filter(pumping_session=pumping).count(), 1
        )

    def test_pumping_oz_normalizes_feed_inventory_amount(self):
        """Pumping in oz normalizes amount to ml in the FeedInventory entry."""
        start = timezone.localtime() - timezone.timedelta(minutes=15)
        end = timezone.localtime() - timezone.timedelta(minutes=10)
        pumping = models.Pumping.objects.create(
            child=self.child,
            start=start,
            end=end,
            amount=3.0,
            amount_unit="oz",
        )
        entry = models.FeedInventory.objects.get(pumping_session=pumping)
        # 3 oz * 29.5735 = 88.7 (rounded to 1 decimal)
        self.assertAlmostEqual(entry.amount, 88.7, places=1)
        self.assertEqual(entry.amount_unit, "ml")

    def test_milk_product_line_get_or_create(self):
        """B5 (2026-08-21): pumping no longer creates a sentinel milk
        ProductLine — FeedInventory rows stand alone."""
        start = timezone.localtime() - timezone.timedelta(minutes=10)
        end = timezone.localtime() - timezone.timedelta(minutes=5)
        models.Pumping.objects.create(
            child=self.child,
            start=start,
            end=end,
            amount=20.0,
        )
        self.assertFalse(
            models.ProductLine.objects.filter(item_type="milk").exists(),
            "sentinel milk ProductLine should not exist",
        )
        self.assertTrue(
            models.FeedInventory.objects.filter(pumping_session__isnull=False).exists()
        )

    def test_pumping_zero_amount_no_feed_inventory(self):
        """Pumping with amount=0 should not create a FeedInventory (edge case)."""
        # amount is FloatField null=False, so 0 is valid but falsy.
        start = timezone.localtime() - timezone.timedelta(minutes=5)
        end = timezone.localtime()
        models.Pumping.objects.create(
            child=self.child,
            start=start,
            end=end,
            amount=0.0,
        )
        # amount_normalized is 0 which is falsy, so no FeedInventory created
        self.assertEqual(models.FeedInventory.objects.count(), 0)
