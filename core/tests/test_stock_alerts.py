# -*- coding: utf-8 -*-
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.inventory import (
    classify_stock_alert,
    compute_diaper_burn_table,
    diaper_stock_threshold,
    next_size_up,
    size_sort_key,
)
from core.models import Child, DiaperChange, ProductLine, SupplyItem

User = get_user_model()


class SizeOrderTests(TestCase):
    def test_size_order(self):
        sizes = ["3", "NB", "1", "P", "5", "2", "4", "weird"]
        self.assertEqual(
            sorted(sizes, key=size_sort_key),
            ["P", "NB", "1", "2", "3", "4", "5", "weird"],
        )


class NextSizeUpTests(TestCase):
    def test_next_size_up(self):
        self.assertEqual(next_size_up("3", ["1", "3", "5", "NB"]), "5")
        self.assertEqual(next_size_up("3", ["1", "NB"]), None)
        self.assertEqual(next_size_up("NB", ["NB", "1"]), "1")


class AlertClassTests(TestCase):
    def test_classify_out(self):
        row = {
            "on_hand": 0,
            "usable": 0,
            "reserve": 0,
            "days_remaining": None,
            "has_usage": True,
        }
        self.assertEqual(classify_stock_alert(row, 3), "out")

    def test_classify_open_reserve(self):
        row = {
            "on_hand": 10,
            "usable": 0,
            "reserve": 10,
            "days_remaining": None,
            "has_usage": True,
        }
        self.assertEqual(classify_stock_alert(row, 3), "open_reserve")

    def test_classify_low(self):
        row = {
            "on_hand": 15,
            "usable": 15,
            "reserve": 0,
            "days_remaining": 2,
            "has_usage": True,
        }
        self.assertEqual(classify_stock_alert(row, 3), "low")
        row2 = {
            "on_hand": 40,
            "usable": 40,
            "reserve": 0,
            "days_remaining": 4,
            "has_usage": True,
        }
        self.assertEqual(classify_stock_alert(row2, 3), None)

    def test_classify_low_boundary_inclusive(self):
        row = {
            "on_hand": 30,
            "usable": 30,
            "reserve": 0,
            "days_remaining": 3,
            "has_usage": True,
        }
        self.assertEqual(classify_stock_alert(row, 3), "low")


class ThresholdTests(TestCase):
    def test_threshold_default_when_unset(self):
        # No dbsetting row written -> default 3
        self.assertEqual(diaper_stock_threshold(), 3)

    def test_threshold_reads_setting(self):
        SupplyItem.settings.low_stock_threshold_days = 5
        try:
            self.assertEqual(diaper_stock_threshold(), 5)
        finally:
            SupplyItem.settings.low_stock_threshold_days = None


def _mk_changes(child, size, n, **kw):
    now = timezone.now()
    return [
        DiaperChange.objects.create(
            child=child,
            time=now - timedelta(minutes=i),
            wet=True,
            solid=False,
            diaper_size=size,
            **kw,
        )
        for i in range(n)
    ]


class BurnTableTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("test-user", password="pw")
        cls.child = Child.objects.create(
            first_name="T",
            last_name="C",
            birth_date=timezone.localdate() - timedelta(days=90),
        )
        cls.pl = ProductLine.objects.create(
            item_type="diapers", brand="TestBrand", line=""
        )

    def test_household_pools_counted_for_child(self):
        """Regression (issue #30): card ignored household (child=None) pools."""
        SupplyItem.objects.create(
            product_line=self.pl, child=None, size="1", quantity=50, initial_quantity=50
        )
        _mk_changes(self.child, "1", 7)
        table = compute_diaper_burn_table(self.child)
        row = next(r for r in table["rows"] if r["size"] == "1")
        self.assertEqual(row["on_hand"], 50)
        self.assertEqual(row["usable"], 50)
        self.assertEqual(row["days_remaining"], 50)

    def test_child_pool_excluded_for_other_child(self):
        other = Child.objects.create(
            first_name="O",
            last_name="K",
            birth_date=timezone.localdate() - timedelta(days=30),
        )
        SupplyItem.objects.create(
            product_line=self.pl, child=other, size="2", quantity=9, initial_quantity=9
        )
        table = compute_diaper_burn_table(self.child)
        self.assertFalse(any(r["size"] == "2" for r in table["rows"]))

    def test_reserve_pool_counted_on_hand_not_usable(self):
        SupplyItem.objects.create(
            product_line=self.pl,
            child=None,
            size="1",
            quantity=100,
            initial_quantity=100,
            is_reserve=True,
        )
        _mk_changes(self.child, "1", 7)  # 1/day
        table = compute_diaper_burn_table(self.child)
        row = next(r for r in table["rows"] if r["size"] == "1")
        self.assertEqual(row["on_hand"], 100)
        self.assertEqual(row["usable"], 0)
        self.assertEqual(row["alert"], "open_reserve")

    def test_open_pool_alert_low_and_next_size_up(self):
        SupplyItem.objects.create(
            product_line=self.pl, child=None, size="1", quantity=3, initial_quantity=3
        )
        SupplyItem.objects.create(
            product_line=self.pl, child=None, size="2", quantity=40, initial_quantity=40
        )
        _mk_changes(self.child, "1", 7)  # 1/day -> 3 days
        table = compute_diaper_burn_table(self.child)
        row = next(r for r in table["rows"] if r["size"] == "1")
        self.assertEqual(row["days_remaining"], 3)
        alert = classify_stock_alert(row, table["threshold_days"])
        self.assertEqual(alert, "low")
        self.assertEqual(next_size_up("1", table["stocked_sizes"]), "2")

    def test_out_of_stock_with_usage(self):
        _mk_changes(self.child, "5", 7)
        table = compute_diaper_burn_table(self.child)
        row = next(r for r in table["rows"] if r["size"] == "5")
        self.assertEqual(row["on_hand"], 0)
        self.assertEqual(row["alert"], "out")

    def test_include_usage_days_adds_row(self):
        # A change 10 days ago: outside the 7d burn window, inside 14d include window
        DiaperChange.objects.create(
            child=self.child,
            time=timezone.now() - timedelta(days=10),
            wet=True,
            solid=False,
            diaper_size="3",
        )
        table = compute_diaper_burn_table(self.child, include_usage_days=14)
        self.assertTrue(any(r["size"] == "3" for r in table["rows"]))
        # without include window: size 3 has no stock and no usage in window -> no row
        table2 = compute_diaper_burn_table(self.child)
        self.assertFalse(any(r["size"] == "3" for r in table2["rows"]))

    def test_span_days_custom_range(self):
        _mk_changes(self.child, "1", 4)
        to_dt = timezone.now() + timedelta(days=1)
        from_dt = timezone.now() - timedelta(days=3)
        table = compute_diaper_burn_table(self.child, from_dt=from_dt, to_dt=to_dt)
        # (now+1d).date() - (now-3d).date() = 4 calendar days, +1 inclusive = 5
        self.assertEqual(table["span_days"], 5)

    def test_household_and_child_pools_sum(self):
        SupplyItem.objects.create(
            product_line=self.pl, child=None, size="1", quantity=10, initial_quantity=10
        )
        SupplyItem.objects.create(
            product_line=self.pl,
            child=self.child,
            size="1",
            quantity=5,
            initial_quantity=5,
        )
        table = compute_diaper_burn_table(self.child)
        row = next(r for r in table["rows"] if r["size"] == "1")
        self.assertEqual(row["on_hand"], 15)


class CardParityTests(TestCase):
    """The dashboard card must show exactly what /supplies shows."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser("card-admin", "a@b.c", "pw")
        cls.child = Child.objects.create(
            first_name="P",
            last_name="Q",
            birth_date=timezone.localdate() - timedelta(days=90),
        )
        cls.pl = ProductLine.objects.create(
            item_type="diapers", brand="ParityBrand", line=""
        )

    def test_card_matches_supplies(self):
        from django.test import Client

        SupplyItem.objects.create(
            product_line=self.pl, child=None, size="1", quantity=30, initial_quantity=30
        )
        _mk_changes(self.child, "1", 7)

        c = Client()
        c.force_login(self.user)
        supplies = c.get("/supplies/").content.decode()
        dash = c.get(f"/children/{self.child.slug}/dashboard/").content.decode()

        # strip tags for text comparison
        import re as _re

        def rows_of(html):
            body = _re.search(
                r"Diaper (?:Inventory Summary|Stock Alerts).*?<tbody>(.*?)</tbody>",
                html,
                _re.S,
            )
            out = []
            for m in _re.finditer(r"<tr[^>]*>(.*?)</tr>", body.group(1), _re.S):
                cells = [
                    _re.sub(r"<[^>]+>", "", x).strip()
                    for x in _re.findall(r"<td[^>]*>(.*?)</td>", m.group(1), _re.S)
                ]
                if cells:
                    out.append(cells)
            return out

        s_rows = rows_of(supplies)
        d_rows = rows_of(dash)
        s_map = {r[0]: r for r in s_rows}
        d_map = {r[0]: r for r in d_rows}
        self.assertEqual(
            set(s_map), set(d_map), "sizes differ between /supplies and card"
        )
        for size in s_map:
            self.assertEqual(s_map[size][1], d_map[size][1], f"{size}: on_hand differs")
