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

    def test_medication_views(self):
        page = self.c.get("/medication/")
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/medication/add/")
        self.assertEqual(page.status_code, 200)

        entry = models.Medication.objects.first()
        page = self.c.get("/medication/{}/".format(entry.id))
        self.assertEqual(page.status_code, 200)
        page = self.c.get("/medication/{}/delete/".format(entry.id))
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


class DevFeatureTemplatesTestCase(TestCase):
    """Regression: dev-feature add/delete pages must render (BD-8, Aug 8 2026).

    The 6 form/confirm-delete templates were missing at the correct path on dev
    (empty strays at core/templates/*.html; prescription_* missing entirely),
    causing TemplateDoesNotExist at /products/add/, /supplies/add/ and
    /prescriptions/add/. These tests pin the URLs to 200.
    """

    @classmethod
    def setUpClass(cls):
        super(DevFeatureTemplatesTestCase, cls).setUpClass()
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
            last_name="Child",
            birth_date=timezone.localdate() - timezone.timedelta(days=90),
        )
        cls.product_line = models.ProductLine.objects.create(
            item_type="formula", brand="Test Brand", line="Test Line"
        )
        cls.supply_item = models.SupplyItem.objects.create(
            child=cls.child,
            product_line=cls.product_line,
            size="NB",
            quantity=10,
            initial_quantity=10,
        )
        cls.prescription = models.Prescription.objects.create(
            child=cls.child, medication_name="Test Med"
        )

    def test_dev_feature_add_and_delete_pages_render(self):
        pages = [
            "/products/add/",
            "/products/{}/delete/".format(self.product_line.pk),
            "/supplies/add/",
            "/supplies/{}/delete/".format(self.supply_item.pk),
            "/prescriptions/add/",
            "/prescriptions/{}/delete/".format(self.prescription.pk),
            # regression: previously-working neighbors stay working
            "/feed-inventory/add/",
            "/equipment/add/",
            "/doctor-visits/add/",
        ]
        for page in pages:
            with self.subTest(page=page):
                self.assertEqual(self.c.get(page).status_code, 200)


class FeedInventoryRenameTestCase(ViewsTestCase):
    """FR-3: 'Feed Inventory' renamed to 'Milk Inventory' in UI (T5)."""

    @classmethod
    def setUpClass(cls):
        super(FeedInventoryRenameTestCase, cls).setUpClass()
        cls.c.login(**cls.credentials)

    def test_list_page_shows_renamed_label(self):
        """List page title/h1 must show the new feature name."""
        resp = self.c.get("/feed-inventory/")
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode("utf-8")
        self.assertIn("Milk Inventory", body)
        # The old labels must no longer appear as UI text (URL paths use
        # lowercase 'feed-inventory' and are fine).
        self.assertNotIn(">Feed Inventory<", body)
        self.assertNotIn("Milk & RTD Formula Inventory", body)

    def test_add_page_shows_renamed_label(self):
        """Add page must show the new feature name in breadcrumbs/title."""
        resp = self.c.get("/feed-inventory/add/")
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode("utf-8")
        self.assertIn("Milk Inventory", body)
        self.assertNotIn(">Feed Inventory<", body)
        self.assertNotIn("Milk & RTD Formula Inventory", body)


class ActiveBottlesCardTestCase(ViewsTestCase):
    """T5: 'Active bottles' dashboard card renders countdowns."""

    @classmethod
    def setUpClass(cls):
        super(ActiveBottlesCardTestCase, cls).setUpClass()
        cls.c.login(**cls.credentials)

    def test_dashboard_renders_active_bottles_card(self):
        from core.models import PreparedFeed, FormulaStock, ProductLine
        from django.utils import timezone as dj_tz

        child = models.Child.objects.first()
        pl = ProductLine.objects.create(
            item_type="formula", brand="Similac", line="360 T5 Test"
        )
        stock = FormulaStock.objects.create(
            product_line=pl, form="powder", container_size=1130.0, quantity=1,
            grams_remaining=1000.0, opened_at=dj_tz.now(),
        )
        unit = PreparedFeed.objects.create(
            source_pool=stock, prepared_from="powder_mix",
            amount=120.0, amount_remaining=90.0, status="active",
            prepared_at=dj_tz.now(),
        )
        try:
            resp = self.c.get(f"/children/{child.slug}/dashboard/")
            self.assertEqual(resp.status_code, 200)
            body = resp.content.decode("utf-8")
            self.assertIn("Active Bottles", body)
            self.assertIn("90.0 ml", body)
            # use_by_info badge text present (room-temp window from prep)
            self.assertIn("Use within", body)
        finally:
            unit.delete()
            stock.delete()
            pl.delete()

    def test_dashboard_card_absent_when_no_units(self):
        # With dashboard_hide_empty enabled and no active units, the
        # card hides entirely (cards/base.html empty gate).
        settings = self.user.settings
        settings.dashboard_hide_empty = True
        settings.save()
        try:
            body = self.c.get(
                f"/children/{models.Child.objects.first().slug}/dashboard/"
            ).content.decode("utf-8")
            self.assertNotIn("Active Bottles", body)
        finally:
            settings.dashboard_hide_empty = False
            settings.save()


class FeedInventoryTypeRetirementTestCase(ViewsTestCase):
    """T5: FeedInventory.type loses 'formula'; legacy rows render."""

    @classmethod
    def setUpClass(cls):
        super(FeedInventoryTypeRetirementTestCase, cls).setUpClass()
        cls.c.login(**cls.credentials)

    def test_type_choices_exclude_formula(self):
        from core.models import FeedInventory
        choices = [c[0] for c in FeedInventory._meta.get_field("type").choices]
        self.assertNotIn("formula", choices)
        self.assertIn("breast_milk", choices)
        self.assertIn("donor_milk", choices)

    def test_type_choices_exclude_formula_form(self):
        from core import forms as core_forms
        f = core_forms.FeedInventoryForm()
        self.assertNotIn("formula", [c[0] for c in f.fields["type"].choices])

    def test_list_page_no_formula_type_label(self):
        resp = self.c.get("/feed-inventory/")
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn(">Formula<", resp.content.decode("utf-8"))


class FeedInventoryConsumeDiscardTestCase(TestCase):
    """FR-5: Consume and Discard views for FeedInventory."""

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
            last_name="Child",
            birth_date=timezone.localdate() - timezone.timedelta(days=30),
        )

    def setUp(self):
        now = timezone.localtime()
        self.pumping = models.Pumping.objects.create(
            child=self.child,
            start=now - timezone.timedelta(minutes=20),
            end=now - timezone.timedelta(minutes=5),
            amount=120.0,
        )
        self.inventory = models.FeedInventory.objects.get(pumping_session=self.pumping)

    def test_timer_quick_add_single_child_despite_stale_cache(self):
        """A1 (views) regression: quick timer add must attach the single
        child based on the real DB count, not Child.count() — the cache
        goes stale when children are deleted in bulk (observed cache=3,
        DB=1), so timers were created unattached."""
        from django.core.cache import cache

        cache.set(models.Child.cache_key_count, 7, None)
        try:
            resp = self.c.post("/timers/add/quick/", follow=True)
            self.assertEqual(resp.status_code, 200)
            timer = models.Timer.objects.order_by("-id").first()
            self.assertEqual(
                timer.child,
                self.child,
                "quick-add timer should attach the single child despite "
                "stale cached count",
            )
        finally:
            cache.delete(models.Child.cache_key_count)

    def test_consume_page_get(self):
        resp = self.c.get("/feed-inventory/{}/consume/".format(self.inventory.pk))
        self.assertEqual(resp.status_code, 200)

    def test_consume_partial_amount(self):
        resp = self.c.post(
            "/feed-inventory/{}/consume/".format(self.inventory.pk),
            {"amount": 30},
        )
        self.assertEqual(resp.status_code, 302)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.amount_remaining, 90.0)
        self.assertEqual(self.inventory.status, "fresh")

    def test_consume_all_marks_used(self):
        resp = self.c.post(
            "/feed-inventory/{}/consume/".format(self.inventory.pk),
            {"amount": 120},
        )
        self.assertEqual(resp.status_code, 302)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.amount_remaining, 0)
        self.assertEqual(self.inventory.status, "used")

    def test_consume_more_than_remaining_rejected(self):
        resp = self.c.post(
            "/feed-inventory/{}/consume/".format(self.inventory.pk),
            {"amount": 200},
        )
        # Form invalid — stays on page (200), not redirect
        self.assertEqual(resp.status_code, 200)
        self.inventory.refresh_from_db()
        # Amount unchanged
        self.assertEqual(self.inventory.amount_remaining, 120.0)

    def test_discard_page_get(self):
        resp = self.c.get("/feed-inventory/{}/discard/".format(self.inventory.pk))
        self.assertEqual(resp.status_code, 200)

    def test_discard_post(self):
        resp = self.c.post(
            "/feed-inventory/{}/discard/".format(self.inventory.pk)
        )
        self.assertEqual(resp.status_code, 302)
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.amount_remaining, 0)
        self.assertEqual(self.inventory.status, "discarded")
