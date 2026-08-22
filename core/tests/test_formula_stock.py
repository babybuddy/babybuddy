# -*- coding: utf-8 -*-
"""
Formula Stock T2 tests - stock page, open flow, manual adjust,
derived clocks (use_by / use_by_info), drain order.

Follows the repo's setUpClass + fake command + superuser pattern
(tests_views.py).
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.test import Client as HttpClient
from django.urls import reverse
from django.utils import timezone

from faker import Faker

from core import models


def _mk_pl(brand, line):
    return models.ProductLine.objects.create(
        brand=brand, line=line, item_type="formula"
    )


def _mk_user():
    fake = Faker()
    fake_user = fake.simple_profile()
    credentials = {
        "username": fake_user["username"],
        "password": fake.password(),
    }
    user = get_user_model().objects.create_user(
        is_superuser=True, **credentials
    )
    return user, credentials
class FormulaStockClockTestCase(TestCase):
    """Derived clock math (CDC/label rules)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("migrate", verbosity=0)
        call_command("fake", verbosity=0)
        cls.user, cls.credentials = _mk_user()
        cls.c = HttpClient()
        cls.pl_powder = _mk_pl("Similac", "360 Total Care")
        cls.pl_rtf = _mk_pl("Enfamil", "NeuroPro RTF")

    def test_sealed_powder_expiry_only(self):
        stock = models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=2,
            expiry_date=(timezone.now() + timedelta(days=400)).date(),
        )
        bound = stock.use_by()
        self.assertIsNotNone(bound)
        self.assertEqual(bound.date(), stock.expiry_date)

    def test_sealed_no_expiry_no_bound(self):
        stock = models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=2,
            expiry_date=None,
        )
        self.assertIsNone(stock.use_by())
        self.assertIsNone(stock.use_by_info())

    def test_opened_powder_one_month_window(self):
        opened_at = timezone.now() - timedelta(days=10)
        stock = models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=1,
            opened_at=opened_at,
            grams_remaining=900.0,
            usage_eligible=opened_at,
        )
        bound = stock.use_by()
        self.assertIsNotNone(bound)
        self.assertAlmostEqual(
            (bound - opened_at).total_seconds(),
            timedelta(days=31).total_seconds(),
            delta=timedelta(days=1).total_seconds(),
        )

    def test_opened_powder_expiry_caps_window(self):
        stock = models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=1,
            opened_at=timezone.now() - timedelta(days=5),
            grams_remaining=900.0,
            expiry_date=(timezone.now() + timedelta(days=3)).date(),
        )
        bound = stock.use_by()
        self.assertEqual(bound.date(), stock.expiry_date)

    def test_opened_rtf_48h_window(self):
        opened_at = timezone.now() - timedelta(hours=50)
        stock = models.FormulaStock.objects.create(
            product_line=self.pl_rtf,
            form="rtf",
            container_size=237.0,
            quantity=1,
            opened_at=opened_at,
            ml_remaining=150.0,
            usage_eligible=opened_at,
        )
        bound = stock.use_by()
        self.assertIsNotNone(bound)
        self.assertEqual(bound - opened_at, timedelta(hours=48))
        info = stock.use_by_info()
        self.assertEqual(info["css_class"], "text-bg-danger")
        self.assertIn("Expired", info["primary_text"])

    def test_opened_rtf_fresh_badge_and_stint_warning(self):
        opened_at = timezone.now() - timedelta(hours=2)
        stock = models.FormulaStock.objects.create(
            product_line=self.pl_rtf,
            form="rtf",
            container_size=237.0,
            quantity=1,
            opened_at=opened_at,
            ml_remaining=200.0,
            usage_eligible=opened_at,
        )
        info = stock.use_by_info()
        self.assertEqual(info["css_class"], "text-bg-warning")
        self.assertTrue(info["stint_warning"])
        self.assertIn("1 h per stint", stock.use_by_tooltip)

    def test_sealed_badge_state_label(self):
        stock = models.FormulaStock.objects.create(
            product_line=self.pl_rtf,
            form="rtf",
            container_size=237.0,
            quantity=3,
            expiry_date=(timezone.now() + timedelta(days=200)).date(),
        )
        info = stock.use_by_info()
        self.assertEqual(info["css_class"], "text-bg-success")
        self.assertIn("Sealed", info["state_label"])
class FormulaStockOpenFlowTestCase(TestCase):
    """open_container() both directions + ledger audit."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("migrate", verbosity=0)
        call_command("fake", verbosity=0)
        cls.user, cls.credentials = _mk_user()
        cls.c = HttpClient()
        cls.pl_powder = _mk_pl("Similac", "360 Total Care")

    def test_open_from_multi_pool_creates_new_row(self):
        pool = models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=3,
            expiry_date=(timezone.now() + timedelta(days=400)).date(),
        )
        opened = pool.open_container()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 2)
        self.assertIsNone(pool.opened_at)
        self.assertIsNotNone(opened.pk)
        self.assertNotEqual(opened.pk, pool.pk)
        self.assertEqual(opened.quantity, 1)
        self.assertEqual(opened.grams_remaining, 1130.0)
        self.assertIsNone(opened.ml_remaining)
        self.assertIsNotNone(opened.opened_at)
        self.assertIsNotNone(opened.usage_eligible)
        pool_events = pool.events.filter(type="opened")
        self.assertTrue(pool_events.exists())
        opened_events = opened.events.filter(type="opened")
        self.assertEqual(opened_events.count(), 1)
        ev = opened_events.first()
        self.assertEqual(ev.grams_after, 1130.0)

    def test_open_from_single_pool_flips_in_place(self):
        pool = models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=1,
        )
        opened = pool.open_container()
        pool.refresh_from_db()
        self.assertEqual(opened.pk, pool.pk)
        self.assertEqual(pool.quantity, 1)
        self.assertIsNotNone(pool.opened_at)
        self.assertEqual(pool.grams_remaining, 1130.0)

    def test_open_rtf_sets_ml(self):
        pl_rtf = _mk_pl("Enfamil", "RTF")
        pool = models.FormulaStock.objects.create(
            product_line=pl_rtf,
            form="rtf",
            container_size=237.0,
            quantity=1,
        )
        opened = pool.open_container()
        self.assertEqual(opened.ml_remaining, 237.0)
        self.assertIsNone(opened.grams_remaining)

    def test_open_already_opened_rejected(self):
        stock = models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=1,
            opened_at=timezone.now(),
            grams_remaining=1000.0,
        )
        with self.assertRaises(ValidationError):
            stock.open_container()

    def test_drain_order(self):
        pl = self.pl_powder
        a = models.FormulaStock.objects.create(
            product_line=pl, form="powder", container_size=100,
            quantity=1, opened_at=timezone.now() - timedelta(hours=2),
            grams_remaining=90,
        )
        b = models.FormulaStock.objects.create(
            product_line=pl, form="powder", container_size=100,
            quantity=1, opened_at=timezone.now() - timedelta(hours=1),
            grams_remaining=95,
        )
        c = models.FormulaStock.objects.create(
            product_line=pl, form="powder", container_size=100,
            quantity=1, opened_at=timezone.now(),
            grams_remaining=99, drain_priority=5,
        )
        ordered = list(models.FormulaStock.drain_ordered_opened_pools())
        self.assertEqual(ordered[0].pk, c.pk)
        self.assertEqual(ordered[1].pk, a.pk)
        self.assertEqual(ordered[2].pk, b.pk)
class FormulaStockViewTestCase(TestCase):
    """List page sections + open/adjust flows through the views."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("migrate", verbosity=0)
        call_command("fake", verbosity=0)
        cls.user, cls.credentials = _mk_user()
        cls.c = HttpClient()
        cls.pl_powder = _mk_pl("Similac", "360 Total Care")
        cls.pool = models.FormulaStock.objects.create(
            product_line=cls.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=2,
        )
        cls.opened = models.FormulaStock.objects.create(
            product_line=cls.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=1,
            opened_at=timezone.now() - timedelta(hours=30),
            grams_remaining=800.0,
        )

    def setUp(self):
        self.c.login(**self.credentials)

    def test_list_renders_both_sections(self):
        page = self.c.get(reverse("core:formulastock-list"))
        self.assertEqual(page.status_code, 200)
        content = page.content.decode()
        self.assertIn("Opened containers", content)
        self.assertIn("Sealed pools", content)
        self.assertIn("800", content)
        self.assertIn("use-by-badge", content)

    def test_open_view_get(self):
        page = self.c.get(
            reverse("core:formulastock-open", args=[self.pool.pk])
        )
        self.assertEqual(page.status_code, 200)

    def test_open_view_post_creates_opened_row(self):
        page = self.c.post(
            reverse("core:formulastock-open", args=[self.pool.pk]),
            {
                "opened_at": timezone.localtime(timezone.now()).strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "note": "test open",
            },
        )
        self.assertRedirects(page, reverse("core:formulastock-list"))
        self.pool.refresh_from_db()
        self.assertEqual(self.pool.quantity, 1)
        self.assertEqual(
            models.FormulaStock.objects.filter(
                opened_at__isnull=False
            ).count(),
            2,
        )
        self.assertTrue(
            models.FormulaStockEvent.objects.filter(
                type="opened", note__contains="test open"
            ).exists()
        )

    def test_adjust_view_post(self):
        page = self.c.post(
            reverse("core:formulastock-adjust", args=[self.opened.pk]),
            {
                "physical_amount": 750.0,
                "reason": "physical_count",
                "note": "",
                "count_time": timezone.localtime(timezone.now()).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            },
        )
        self.assertRedirects(page, reverse("core:formulastock-list"))
        self.opened.refresh_from_db()
        self.assertEqual(self.opened.grams_remaining, 750.0)
        ev = models.FormulaStockEvent.objects.filter(
            stock=self.opened, type="manual_adjust"
        ).latest("created_at")
        self.assertEqual(ev.delta_grams, -50.0)
        self.assertEqual(ev.grams_after, 750.0)

    def test_adjust_rejects_sealed(self):
        page = self.c.post(
            reverse("core:formulastock-adjust", args=[self.pool.pk]),
            {
                "physical_amount": 1000.0,
                "reason": "physical_count",
                "note": "",
                "count_time": timezone.localtime(timezone.now()).strftime(
                    "%Y-%m-%d %H:%M"
                ),
            },
        )
        self.assertEqual(page.status_code, 200)
        self.pool.refresh_from_db()
        self.assertEqual(self.pool.quantity, 2)



class InlinePrepFeedingTestCase(TestCase):
    """T6 — inline prep at feed time (issue #53).

    Powder pick + amount mixed > amount fed creates a PreparedFeed unit;
    pool decrements grams for the FULL mixed amount; blank/==fed keeps
    direct-pool behavior.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("migrate", verbosity=0)
        call_command("fake", verbosity=0)
        cls.user, cls.credentials = _mk_user()
        cls.c = HttpClient()
        cls.pl_powder = _mk_pl("Similac", "360 Total Care")
        cls.pl_powder.scoop_grams = 8.7
        cls.pl_powder.water_per_scoop_ml = 60.0
        cls.pl_powder.save()

    def _mk_pool(self, grams=1000.0):
        return models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=1,
            opened_at=timezone.now(),
            grams_remaining=grams,
        )

    def _feed(self, pool, amount, unit="ml", **extra):
        return models.Feeding.objects.create(
            child=models.Child.objects.first(),
            start=timezone.now(),
            end=timezone.now(),
            type="formula",
            method="bottle",
            amount=amount,
            amount_unit=unit,
            formula_stock=pool,
            **extra,
        )

    def test_powder_pick_no_mixed_creates_no_unit(self):
        """Blank: direct-pool behavior — no unit, grams for fed only."""
        pool = self._mk_pool()
        feed = self._feed(pool, 60.0)
        pool.refresh_from_db()
        self.assertFalse(
            models.PreparedFeed.objects.exists(),
            "no-unit path must not create a PreparedFeed",
        )
        # grams for fed only: 60 * 8.7/60 = 8.7g
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 8.7)
        self.assertIsNone(feed.prepared_feed_id)
        self.assertEqual(feed.formula_stock_id, pool.pk)

    def test_powder_pick_mixed_equals_fed_creates_no_unit(self):
        """Explicit mixed == fed: still direct-pool (no unit)."""
        pool = self._mk_pool()
        feed = self._feed(pool, 60.0, amount_mixed=60.0)
        pool.refresh_from_db()
        self.assertFalse(models.PreparedFeed.objects.exists())
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 8.7)
        self.assertIsNone(feed.prepared_feed_id)

    def test_powder_pick_mixed_gt_fed_creates_unit(self):
        """mixed > fed: unit created, pool grams for FULL mixed, unit
        carries leftover + clocks, feeding linked to the unit."""
        pool = self._mk_pool()
        feed = self._feed(pool, 60.0, amount_mixed=120.0)
        pool.refresh_from_db()
        unit = models.PreparedFeed.objects.get()
        self.assertEqual(unit.source_pool_id, pool.pk)
        self.assertEqual(unit.prepared_from, "powder_mix")
        self.assertEqual(unit.amount, 120.0)
        # unit fed consumption: 120 - 60 = 60 left
        self.assertAlmostEqual(unit.amount_remaining, 60.0)
        self.assertEqual(unit.status, "active")
        # pool decremented grams for FULL mixed: 120 * 8.7/60 = 17.4g
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 17.4)
        # feeding linked to the unit, not the pool
        feed.refresh_from_db()
        self.assertEqual(feed.prepared_feed_id, unit.pk)
        self.assertIsNone(feed.formula_stock_id)
        # ledger: pool prep_decrement (grams) + unit feeding_decrement (ml)
        pool_ev = pool.events.filter(type="prep_decrement")
        self.assertTrue(pool_ev.exists())
        self.assertAlmostEqual(pool_ev.first().delta_grams, -17.4)
        unit_ev = unit.events.filter(type="feeding_decrement")
        self.assertTrue(unit_ev.exists())
        self.assertAlmostEqual(unit_ev.first().delta_ml, -60.0)

    def test_powder_pick_mixed_gt_fed_oz_fed(self):
        """Fed in oz, mixed in ml — comparison uses normalized ml."""
        pool = self._mk_pool()
        self._feed(pool, 2.0, unit="oz", amount_mixed=120.0)
        unit = models.PreparedFeed.objects.get()
        # fed 2oz = 59.1ml; unit has 120-59.1 = 60.9ml left
        self.assertAlmostEqual(unit.amount_remaining, 60.9, places=1)
        # grams for full mixed: 120 * 8.7/60 = 17.4
        pool.refresh_from_db()
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 17.4)

    def test_rtf_source_never_creates_unit(self):
        """RTF pour: amount_mixed ignored — no unit ever."""
        pl_rtf = _mk_pl("Enfamil", "RTF")
        pool = models.FormulaStock.objects.create(
            product_line=pl_rtf,
            form="rtf",
            container_size=237.0,
            quantity=1,
            opened_at=timezone.now(),
            ml_remaining=237.0,
        )
        self._feed(pool, 60.0, amount_mixed=120.0)
        pool.refresh_from_db()
        self.assertFalse(models.PreparedFeed.objects.exists())
        self.assertAlmostEqual(pool.ml_remaining, 237.0 - 60.0)


class InlinePrepEditTestCase(TestCase):
    """T6 — edit re-derivation (issue #53 edge cases).

    Edits of a unit-linked feeding must re-derive BOTH the unit ml and
    the pool grams; delete leaves the unit (the mix physically
    happened).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command("migrate", verbosity=0)
        call_command("fake", verbosity=0)
        cls.user, cls.credentials = _mk_user()
        cls.pl_powder = _mk_pl("Similac", "360 Total Care")
        cls.pl_powder.scoop_grams = 8.7
        cls.pl_powder.water_per_scoop_ml = 60.0
        cls.pl_powder.save()

    def _mk_pool(self, grams=1000.0):
        return models.FormulaStock.objects.create(
            product_line=self.pl_powder,
            form="powder",
            container_size=1130.0,
            quantity=1,
            opened_at=timezone.now(),
            grams_remaining=grams,
        )

    def _create_inline(self, pool, fed=60.0, mixed=120.0):
        return models.Feeding.objects.create(
            child=models.Child.objects.first(),
            start=timezone.now(),
            end=timezone.now(),
            type="formula",
            method="bottle",
            amount=fed,
            amount_unit="ml",
            formula_stock=pool,
            amount_mixed=mixed,
        )

    def test_edit_amount_fed_rederives_unit(self):
        """Fed 60→40: unit remaining 60→80; pool grams unchanged (mixed
        unchanged); restore-then-decrement nets the fed delta."""
        pool = self._mk_pool()
        feed = self._create_inline(pool)
        unit = models.PreparedFeed.objects.get()
        self.assertAlmostEqual(unit.amount_remaining, 60.0)

        feed.amount = 40.0
        feed.save()
        unit.refresh_from_db()
        pool.refresh_from_db()
        # restore 60, decrement 40 → remaining 80
        self.assertAlmostEqual(unit.amount_remaining, 80.0)
        # pool: full mixed grams once (unchanged on fed edit)
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 17.4)

    def test_edit_amount_mixed_rederives_pool(self):
        """Mixed 120→180: unit amount 120→180, remaining 60→120; pool
        grams restore 17.4, decrement 26.1 → net -26.1 from 1000."""
        pool = self._mk_pool()
        feed = self._create_inline(pool)
        unit = models.PreparedFeed.objects.get()

        feed.amount_mixed = 180.0
        feed.save()
        unit.refresh_from_db()
        pool.refresh_from_db()
        self.assertAlmostEqual(unit.amount, 180.0)
        self.assertAlmostEqual(unit.amount_remaining, 120.0)
        # 180 * 8.7/60 = 26.1
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 26.1)

    def test_edit_unlink_unit_persists_with_mix(self):
        """Edit clearing the source (picker blank): fed ml restored to the
        unit; unit PERSISTS with its pool provenance (unmixing is not a
        thing — same philosophy as the delete edge); pool keeps the mixed
        grams. The unit stays pickable for continuation feedings."""
        pool = self._mk_pool()
        feed = self._create_inline(pool)
        unit = models.PreparedFeed.objects.get()

        feed.prepared_feed = None
        feed.amount_mixed = None
        feed.save()
        unit.refresh_from_db()
        pool.refresh_from_db()
        # fed ml restored to unit: 60 leftover + 60 restored = 120
        self.assertAlmostEqual(unit.amount_remaining, 120.0)
        self.assertEqual(unit.status, "active")
        self.assertEqual(unit.source_pool_id, pool.pk)
        # pool keeps the mixed grams (the mix physically happened)
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 17.4)

    def test_delete_feeding_unit_survives(self):
        """Delete: unit persists (the mix physically happened); #49
        restore returns the FED ml to the unit."""
        pool = self._mk_pool()
        feed = self._create_inline(pool)
        unit = models.PreparedFeed.objects.get()

        feed.delete()
        unit.refresh_from_db()
        self.assertTrue(
            models.PreparedFeed.objects.filter(pk=unit.pk).exists(),
            "unit must survive feeding delete",
        )
        # #49: the fed ml is restored to the bottle (60 + 60).
        self.assertAlmostEqual(unit.amount_remaining, 120.0)
        # pool grams stay decremented for the mix (physical fact)
        pool.refresh_from_db()
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 17.4)

    def test_edit_to_mixed_eq_fed_collapses_unit(self):
        """Edit reducing mixed to == fed: unit collapses via amount→fed,
        remaining→0, consumed flip. (Unit persists as a zero-left
        consumed record.)"""
        pool = self._mk_pool()
        feed = self._create_inline(pool)
        unit = models.PreparedFeed.objects.get()

        feed.amount_mixed = 60.0
        feed.save()
        unit.refresh_from_db()
        pool.refresh_from_db()
        self.assertAlmostEqual(unit.amount, 60.0)
        self.assertAlmostEqual(unit.amount_remaining, 0.0)
        self.assertEqual(unit.status, "consumed")
        # pool: restore 17.4, decrement 8.7 → 1000 - 8.7
        self.assertAlmostEqual(pool.grams_remaining, 1000.0 - 8.7)
