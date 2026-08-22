"""#49 — Feeding delete restores consumed inventory (milk + formula)."""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core import models


class MilkDeleteRestoreTests(TestCase):
    """Deleting a feeding restores its milk unit consumption."""

    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="Test", birth_date=timezone.now() - timedelta(days=30)
        )

    def _unit(self, remaining=50.0):
        return models.FeedInventory.objects.create(
            child=self.child,
            type="breast_milk",
            amount=50,
            amount_remaining=remaining,
            storage_location="fridge",
            status="fresh",
        )

    def _feeding(self, **kwargs):
        return models.Feeding.objects.create(
            child=self.child,
            start=timezone.now(),
            end=timezone.now() + timedelta(minutes=10),
            type="breast milk",
            method="bottle",
            amount=kwargs.pop("amount", 30.0),
            amount_unit="ml",
            **kwargs,
        )

    def test_delete_restores_milk_unit(self):
        unit = self._unit()
        feeding = self._feeding(feed_inventory=unit)
        unit.refresh_from_db()
        self.assertEqual(unit.amount_remaining, 20.0)
        feeding.delete()
        unit.refresh_from_db()
        self.assertEqual(unit.amount_remaining, 50.0)
        event = unit.events.filter(type="feeding_restored").latest("id")
        self.assertEqual(event.amount_delta, 30.0)

    def test_delete_without_link_is_noop(self):
        feeding = self._feeding()
        feeding.delete()  # must not raise

    def test_delete_with_deleted_unit_is_noop(self):
        unit = self._unit()
        feeding = self._feeding(feed_inventory=unit)
        unit.delete()  # FK is SET_NULL on the feeding row
        feeding.delete()  # must not raise

    def test_edit_then_delete_nets_exact_restore(self):
        unit = self._unit()
        feeding = self._feeding(feed_inventory=unit)
        unit.refresh_from_db()
        # correct the log: 30 -> 45 (engine restores 30, takes 45)
        feeding.amount = 45.0
        feeding.save()
        unit.refresh_from_db()
        self.assertEqual(unit.amount_remaining, 5.0)
        feeding.delete()
        unit.refresh_from_db()
        self.assertEqual(unit.amount_remaining, 50.0)


class PreparedDeleteRestoreTests(TestCase):
    """Deleting a feeding restores a prepared bottle (+T4 lifecycle)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pl = models.ProductLine.objects.create(
            brand="Similac", line="360 Total Care", item_type="formula"
        )

    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="Test", birth_date=timezone.now() - timedelta(days=30)
        )
        self.pool = models.FormulaStock.objects.create(
            product_line=self.pl,
            form="powder",
            container_size=1130.0,
            quantity=1,
            grams_remaining=1000.0,
            opened_at=timezone.now(),
        )

    def _bottle(self, amount=100.0, remaining=70.0, status="active"):
        return models.PreparedFeed.objects.create(
            source_pool=self.pool,
            prepared_from="powder_mix",
            amount=amount,
            amount_remaining=remaining,
            status=status,
            prepared_at=timezone.now(),
        )

    def _feeding_for(self, bottle, fed=30.0):
        return models.Feeding.objects.create(
            child=self.child,
            start=timezone.now(),
            end=timezone.now() + timedelta(minutes=10),
            type="formula",
            method="bottle",
            amount=fed,
            amount_unit="ml",
            prepared_feed=bottle,
        )

    def test_delete_restores_prepared_bottle(self):
        bottle = self._bottle(amount=100.0, remaining=70.0)
        feeding = self._feeding_for(bottle)
        bottle.refresh_from_db()
        self.assertEqual(bottle.amount_remaining, 40.0)
        feeding.delete()
        bottle.refresh_from_db()
        self.assertEqual(bottle.amount_remaining, 70.0)

    def test_delete_flips_auto_consumed_bottle_to_active(self):
        bottle = self._bottle(amount=30.0, remaining=0.0, status="consumed")
        feeding = self._feeding_for(bottle, fed=30.0)
        feeding.delete()
        bottle.refresh_from_db()
        self.assertEqual(bottle.status, "active")
        self.assertEqual(bottle.amount_remaining, 30.0)

    def test_manual_discard_never_flipped_back(self):
        bottle = self._bottle(amount=100.0, remaining=40.0, status="discarded")
        feeding = self._feeding_for(bottle)
        feeding.delete()
        bottle.refresh_from_db()
        self.assertEqual(bottle.status, "discarded")


class FormulaStockDeleteRestoreTests(TestCase):
    """Deleting a feeding restores RTF ml / powder grams to the pool."""

    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="Test", birth_date=timezone.now() - timedelta(days=30)
        )

    def _pool(self, form, **extra):
        pl = models.ProductLine.objects.create(
            brand="TestBrand", line="L-%s" % form, item_type="formula"
        )
        defaults = dict(
            product_line=pl,
            form=form,
            container_size=1130.0,
            quantity=1,
            opened_at=timezone.now(),
        )
        defaults.update(extra)
        return models.FormulaStock.objects.create(**defaults)

    def _feeding(self, pool, amount):
        return models.Feeding.objects.create(
            child=self.child,
            start=timezone.now(),
            end=timezone.now(),
            type="formula",
            method="bottle",
            amount=amount,
            amount_unit="ml",
            formula_stock=pool,
        )

    def test_delete_restores_rtf_pool_ml(self):
        pool = self._pool("rtf", ml_remaining=200.0)
        feeding = self._feeding(pool, 60.0)
        pool.refresh_from_db()
        self.assertEqual(pool.ml_remaining, 140.0)
        feeding.delete()
        pool.refresh_from_db()
        self.assertEqual(pool.ml_remaining, 200.0)

    def test_delete_restores_powder_pool_grams(self):
        pl = models.ProductLine.objects.create(
            brand="TestBrand",
            line="L-powder-ratio",
            item_type="formula",
            scoop_grams=8.7,
            water_per_scoop_ml=60,
        )
        pool = models.FormulaStock.objects.create(
            product_line=pl,
            form="powder",
            container_size=1130.0,
            quantity=1,
            opened_at=timezone.now(),
            grams_remaining=400.0,
        )
        feeding = self._feeding(pool, 120.0)  # 17.4 g
        pool.refresh_from_db()
        self.assertAlmostEqual(pool.grams_remaining, 382.6, places=2)
        feeding.delete()
        pool.refresh_from_db()
        self.assertAlmostEqual(pool.grams_remaining, 400.0, places=2)
