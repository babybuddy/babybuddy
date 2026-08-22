"""Household-scoped supply inventory tests.

SupplyItem pools with child=None are household stock: any child's diaper
changes drain them (signals), recalc counts every child's changes against
them, and every child's inventory page shows them. Child-scoped pools only
match their own child's changes.
"""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from core.models import Child, DiaperChange, ProductLine, SupplyItem


class HouseholdSignalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pl = ProductLine.objects.create(
            item_type="diapers", brand="Pampers", line="Swaddlers"
        )
        cls.child_a = Child.objects.create(
            first_name="A", birth_date="2026-05-25"
        )
        cls.child_b = Child.objects.create(
            first_name="B", birth_date="2026-05-25"
        )
        cls.eligible = timezone.now() - timedelta(days=10)

    def _pool(self, child, qty=5):
        return SupplyItem.objects.create(
            child=child,
            product_line=self.pl,
            size="NB",
            quantity=qty,
            initial_quantity=qty,
            usage_eligible=self.eligible,
        )

    def _change(self, child, brand="Pampers", line="Swaddlers", time=None):
        return DiaperChange.objects.create(
            child=child,
            time=time or timezone.now(),
            wet=False,
            solid=False,
            diaper_size="NB",
            diaper_brand=brand,
            diaper_line=line,
        )

    def test_household_pool_drains_for_any_child(self):
        pool = self._pool(child=None)
        self._change(self.child_a)
        self._change(self.child_b)
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 3)

    def test_child_scoped_pool_only_drains_for_own_child(self):
        pool = self._pool(child=self.child_a)
        self._change(self.child_b)  # not child A — must not touch A's pool
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 5)

    def test_tracking_start_floor_blocks_decrement(self):
        self.child_b.inventory_tracking_start = timezone.now()
        self.child_b.save()
        pool = self._pool(child=None)
        self._change(self.child_b, time=timezone.now() - timedelta(days=1))
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 5)

    def test_delete_restores_household_pool(self):
        pool = self._pool(child=None)
        ch = self._change(self.child_a)
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 4)
        ch.delete()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 5)


class HouseholdRecalcTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.pl = ProductLine.objects.create(
            item_type="diapers", brand="Huggies", line="Little Snugglers"
        )
        cls.child_a = Child.objects.create(
            first_name="A", birth_date="2026-05-25"
        )
        cls.child_b = Child.objects.create(
            first_name="B", birth_date="2026-05-25"
        )
        cls.eligible = timezone.now() - timedelta(days=10)

    def test_recalc_counts_all_children_against_household_pool(self):
        pool = SupplyItem.objects.create(
            child=None,
            product_line=self.pl,
            size="NB",
            quantity=5,
            initial_quantity=5,
            usage_eligible=self.eligible,
        )
        for child in (self.child_a, self.child_b):
            DiaperChange.objects.create(
                child=child,
                time=timezone.now(),
                wet=False,
                solid=False,
                diaper_size="NB",
                diaper_brand="Huggies",
                diaper_line="Little Snugglers",
            )
        # signal already drained both
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 3)

        from core.management.commands.recalculate_inventory import (
            recalculate_inventory,
        )

        recalculate_inventory()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 3)  # recalc agrees: 5 - 2 = 3

    def test_recalc_ignores_changes_below_child_floor(self):
        self.child_b.inventory_tracking_start = timezone.now()
        self.child_b.save()
        pool = SupplyItem.objects.create(
            child=None,
            product_line=self.pl,
            size="NB",
            quantity=5,
            initial_quantity=5,
            usage_eligible=self.eligible,
        )
        # change logged before child B's tracking start — counts for nothing
        DiaperChange.objects.create(
            child=self.child_b,
            time=timezone.now() - timedelta(days=1),
            wet=False,
            solid=False,
            diaper_size="NB",
            diaper_brand="Huggies",
            diaper_line="Little Snugglers",
        )

        from core.management.commands.recalculate_inventory import (
            recalculate_inventory,
        )

        recalculate_inventory()
        pool.refresh_from_db()
        self.assertEqual(pool.quantity, 5)


class HouseholdViewAndFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser(
            username="t", email="t@t.com", password="x" * 12
        )
        cls.pl = ProductLine.objects.create(
            item_type="diapers", brand="Pampers", line="Swaddlers"
        )
        cls.child = Child.objects.create(
            first_name="Test", birth_date="2026-05-25"
        )

    def test_supply_list_includes_household_pools(self):
        SupplyItem.objects.create(
            child=None,
            product_line=self.pl,
            size="NB",
            quantity=2,
            initial_quantity=2,
        )
        c = Client()
        c.force_login(self.user)
        resp = c.get(reverse("core:supplyitem-list"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Pampers", html)  # household pool visible
        items = resp.context["grouped_supplies"]["Diapers"]["Pampers"]["Swaddlers"]
        self.assertEqual(len(items), 1)

    def test_add_form_child_optional_with_household_label(self):
        from core.forms import SupplyItemForm

        form = SupplyItemForm()
        self.assertFalse(form.fields["child"].required)
        rendered = str(form["child"])
        self.assertIn("— Household —", rendered)

    def test_add_form_accepts_no_child(self):
        from core.forms import SupplyItemForm

        form = SupplyItemForm(
            data={
                "child": "",
                "product_line": self.pl.id,
                "size": "NB",
                "acquisition_date": "",
                "usage_eligible": "",
                "is_reserve": False,
                "drain_priority": 0,
                "number_of_packs": 1,
                "items_per_pack": 9,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        obj = form.save()
        self.assertIsNone(obj.child)
        self.assertEqual(obj.quantity, 9)
