"""Sealed-pool decrement semantics (v4 backlog #11).

Sealed (usage_eligible=None, is_reserve=False) ≠ reserve:
- Branded changes (brand+line+size) MAY drain a sealed pool of that
  exact product — a conscious selection — and stamp it open at the
  change's time.
- Generic size-only changes NEVER drain sealed pools.
- Reserve pools are never drained by anything.

Also covers the transaction-based restore: deleting a change reverses
the exact pool its decrement touched, not whatever the matcher would
pick today.
"""
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from core.models import (
    Child,
    DiaperChange,
    InventoryTransaction,
    ProductLine,
    SupplyItem,
)


def _recalc():
    from core.management.commands.recalculate_inventory import (
        recalculate_inventory,
    )

    return recalculate_inventory()


class SealedPoolSignalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pl = ProductLine.objects.create(
            item_type="diapers", brand="Rascals", line="Premium"
        )
        cls.other_pl = ProductLine.objects.create(
            item_type="diapers", brand="Pampers", line="Swaddlers"
        )
        cls.child = Child.objects.create(
            first_name="K", birth_date="2026-05-25"
        )
        cls.acquired = timezone.now() - timedelta(days=30)

    def _sealed(self, pl=None, qty=10):
        return SupplyItem.objects.create(
            child=None,
            product_line=pl or self.pl,
            size="NB",
            quantity=qty,
            initial_quantity=qty,
            usage_eligible=None,
            acquisition_date=self.acquired,
        )

    def _open(self, pl=None, qty=10):
        return SupplyItem.objects.create(
            child=None,
            product_line=pl or self.pl,
            size="NB",
            quantity=qty,
            initial_quantity=qty,
            usage_eligible=timezone.now() - timedelta(days=10),
        )

    def _change(self, brand="Rascals", line="Premium", time=None):
        return DiaperChange.objects.create(
            child=self.child,
            time=time or timezone.now(),
            wet=False,
            solid=False,
            diaper_size="NB",
            diaper_brand=brand,
            diaper_line=line,
        )

    def test_branded_change_drains_sealed_pool_and_stamps_open(self):
        pool = self._sealed(qty=10)
        t = timezone.now()
        self._change(time=t)
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 9)
        self.assertIsNotNone(pool.usage_eligible)
        self.assertEqual(pool.usage_eligible, t)
        tx = InventoryTransaction.objects.filter(
            supply_item=pool, transaction_type="decrement"
        ).first()
        self.assertIsNotNone(tx)
        self.assertIn("Auto-opened", tx.note)

    def test_generic_change_never_drains_sealed_pool(self):
        pool = self._sealed(qty=10)
        DiaperChange.objects.create(
            child=self.child,
            time=timezone.now(),
            wet=False,
            solid=False,
            diaper_size="NB",
        )
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 10)
        self.assertIsNone(pool.usage_eligible)

    def test_branded_change_of_other_product_never_drains_sealed_pool(self):
        pool = self._sealed(qty=10)  # Rascals Premium
        self._change(brand="Pampers", line="Swaddlers")
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 10)
        self.assertIsNone(pool.usage_eligible)

    def test_open_pool_preferred_over_sealed(self):
        open_pool = self._open(qty=2)
        sealed_pool = self._sealed(qty=10)
        self._change()
        self._change()  # open pool now 0
        open_pool.refresh_from_db()
        sealed_pool.refresh_from_db()
        self.assertEqual(open_pool.quantity, 0)
        self.assertIsNone(sealed_pool.usage_eligible)
        third = self._change()  # must fall through to the sealed pool
        sealed_pool.refresh_from_db()
        self.assertEqual(sealed_pool.quantity, 9)
        self.assertEqual(sealed_pool.usage_eligible, third.time)

    def test_sealed_pool_not_drained_before_acquisition_date(self):
        pool = self._sealed(qty=10)
        early = timezone.now() - timedelta(days=45)
        self._change(time=early)
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 10)
        self.assertIsNone(pool.usage_eligible)

    def test_reserve_pool_never_drained_even_branded(self):
        pool = SupplyItem.objects.create(
            child=None,
            product_line=self.pl,
            size="NB",
            quantity=10,
            initial_quantity=10,
            usage_eligible=None,
            acquisition_date=self.acquired,
            is_reserve=True,
        )
        self._change()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 10)
        self.assertIsNone(pool.usage_eligible)

    def test_delete_restores_exact_pool_via_transaction(self):
        pool_a = self._open(qty=1)
        pool_b = self._open(qty=5)
        change = self._change()  # drained pool A (open, earliest) to 0
        pool_a.refresh_from_db()
        self.assertEqual(pool_a.quantity, 0)

        change.delete()
        pool_a.refresh_from_db()
        pool_b.refresh_from_db()
        # Restore must land on pool A (the decremented pool), not B
        # (the pool the matcher would pick today with A empty).
        self.assertEqual(pool_a.quantity, 1)
        self.assertEqual(pool_b.quantity, 5)

    def test_delete_of_never_decremented_change_is_noop(self):
        pool = self._open(qty=5)
        change = DiaperChange.objects.create(
            child=self.child,
            time=timezone.now(),
            wet=False,
            solid=False,
            diaper_size="3",  # no pool of size 3 exists
            diaper_brand="Rascals",
            diaper_line="Premium",
        )
        change.delete()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 5)


class SealedPoolRecalcTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pl = ProductLine.objects.create(
            item_type="diapers", brand="Rascals", line="Premium"
        )
        cls.child = Child.objects.create(
            first_name="K", birth_date="2026-05-25"
        )
        cls.acquired = timezone.now() - timedelta(days=30)

    def _sealed(self, qty=10):
        return SupplyItem.objects.create(
            child=None,
            product_line=self.pl,
            size="NB",
            quantity=qty,
            initial_quantity=qty,
            usage_eligible=None,
            acquisition_date=self.acquired,
        )

    def _change(self, time):
        return DiaperChange.objects.create(
            child=self.child,
            time=time,
            wet=False,
            solid=False,
            diaper_size="NB",
            diaper_brand="Rascals",
            diaper_line="Premium",
        )

    def test_recalc_branded_drains_sealed_and_stamps_open(self):
        pool = self._sealed(qty=10)
        t1 = timezone.now() - timedelta(days=5)
        t2 = timezone.now() - timedelta(days=3)
        self._change(t1)
        self._change(t2)  # signal already drained + stamped
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 8)

        _recalc()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 8)  # agrees with signals, no drift
        self.assertEqual(pool.usage_eligible, t1)  # opened at first change

    def test_recalc_generic_never_touches_sealed(self):
        pool = self._sealed(qty=10)
        DiaperChange.objects.create(
            child=self.child,
            time=timezone.now(),
            wet=False,
            solid=False,
            diaper_size="NB",
        )
        _recalc()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 10)
        self.assertIsNone(pool.usage_eligible)

    def test_recalc_stamps_and_counts_untracked_sealed_consumption(self):
        # Simulate a pool whose history predates the signal (created with
        # wrong state): recalc must count branded changes and open it.
        pool = self._sealed(qty=10)
        t1 = timezone.now() - timedelta(days=5)
        t2 = timezone.now() - timedelta(days=3)
        # changes created while pool had stock but signal skipped sealed
        # pools (pre-fix behavior): quantity stayed 10
        self._change(t1)
        self._change(t2)
        pool.quantity = 10
        pool.usage_eligible = None
        pool.save()

        _recalc()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 8)
        self.assertEqual(pool.usage_eligible, t1)
        tx = InventoryTransaction.objects.filter(
            supply_item=pool, transaction_type="recalc"
        ).first()
        self.assertIsNotNone(tx)
        self.assertIn("opened", tx.note)


class RequiredSizeWidgetTests(TestCase):
    def test_diaper_size_pills_are_focusable_when_required(self):
        from core.forms import DiaperChangeForm

        form = DiaperChangeForm()
        self.assertTrue(form.fields["diaper_size"].required)
        rendered = str(form["diaper_size"])
        self.assertIn("visually-hidden", rendered)
        self.assertNotIn("d-none", rendered)
