from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.forms import BottleFeedingForm, PreparedFeedForm
from core.models import Child, FeedInventory, Feeding, FormulaStock, ProductLine

User = get_user_model()


class RefreezeBlockTests(TestCase):
    """A1: thawed milk can never return to a freezer (CDC)."""

    def setUp(self):
        self.user = User.objects.create_superuser("tester", "t@e.st", "pw")
        self.child = Child.objects.create(
            first_name="Test", birth_date=timezone.now() - timedelta(days=30)
        )

    def _frozen_unit(self):
        return FeedInventory.objects.create(
            child=self.child,
            type="breast_milk",
            amount=50,
            amount_remaining=50,
            storage_location="freezer",
            status="frozen",
            freezer_entered_at=timezone.now() - timedelta(days=10),
        )

    def test_transition_mutate_blocks_refreeze(self):
        unit = self._frozen_unit()
        # freezer → fridge: thaw begins, then refreeze is BLOCKED.
        unit._transition_mutate("fridge", timezone.now())
        unit.save()
        self.assertEqual(unit.status, "thawed")
        self.assertIsNotNone(unit.thaw_started_at)
        with self.assertRaises(ValidationError):
            unit._transition_mutate("freezer", timezone.now())

    def test_clean_blocks_refreeze_on_thawed_status(self):
        unit = self._frozen_unit()
        unit.thaw_started_at = timezone.now()
        unit.status = "thawed"
        unit.storage_location = "fridge"
        unit.full_clean()  # fridge is fine for thawed
        unit.storage_location = "freezer"
        with self.assertRaises(ValidationError):
            unit.full_clean()

    def test_update_view_blocks_refreeze(self):
        unit = self._frozen_unit()
        unit._transition_mutate("fridge", timezone.now())
        unit.save()
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("core:feedinventory-update", args=[unit.pk]),
            {
                "child": self.child.pk,
                "type": "breast_milk",
                "storage_location": "freezer",
                "status": "frozen",
                "amount": 50,
                "amount_remaining": 50,
            },
            follow=True,
        )
        # Guard rejects the edit (200 = re-rendered form with error).
        self.assertEqual(resp.status_code, 200)
        unit.refresh_from_db()
        self.assertEqual(unit.storage_location, "fridge")

    def test_transition_mutate_allows_fresh_to_freezer(self):
        unit = FeedInventory.objects.create(
            child=self.child,
            type="breast_milk",
            amount=50,
            amount_remaining=50,
            storage_location="room_temp",
            status="fresh",
        )
        old_loc, old_status, events = unit._transition_mutate(
            "freezer", timezone.now()
        )
        self.assertEqual(unit.status, "frozen")


class ReserveExclusionTests(TestCase):
    """A2: reserves are never decrementable — auto-pick, pickers, listings."""

    def setUp(self):
        self.user = User.objects.create_user("tester")
        self.line = ProductLine.objects.create(
            item_type="formula",
            brand="TestBrand",
            line="TestLine",
        )

    def _pool(self, reserve=False, drain_priority=0, opened_days_ago=1):
        return FormulaStock.objects.create(
            product_line=self.line,
            form="powder",
            container_size=400,
            quantity=1,
            opened_at=timezone.now() - timedelta(days=opened_days_ago),
            grams_remaining=400,
            drain_priority=drain_priority,
            is_reserve=reserve,
        )

    def test_auto_pick_skips_reserve_even_when_sole_pool(self):
        pool = self._pool(reserve=True)
        feeding = Feeding(
            child=None,
            type="formula",
            formula_brand="TestBrand",
            amount=30,
        )
        self.assertIsNone(feeding._resolve_formula_stock())

    def test_auto_pick_prefers_non_reserve(self):
        normal = self._pool(reserve=False, opened_days_ago=5)
        reserve = self._pool(reserve=True, opened_days_ago=1)
        feeding = Feeding(
            child=None,
            type="formula",
            formula_brand="TestBrand",
            amount=30,
        )
        picked = feeding._resolve_formula_stock()
        self.assertIsNotNone(picked)
        self.assertEqual(picked.pk, normal.pk)

    def test_reserve_not_in_feeding_source_picker(self):
        normal = self._pool()
        reserve = self._pool(reserve=True)
        child = Child.objects.create(
            first_name="T2", birth_date=timezone.now() - timedelta(days=30)
        )
        f = BottleFeedingForm()
        stock_values = [
            v
            for _group, opts in f.fields["formula_source"].choices
            if isinstance(opts, (list, tuple))
            for v, _label in opts
        ]
        self.assertNotIn(f"rtf:{reserve.pk}", stock_values)
        self.assertNotIn(f"powder:{reserve.pk}", stock_values)
        normal_values = [v for v in stock_values if v.startswith(("rtf:", "powder:"))]
        self.assertIn(f"powder:{normal.pk}", normal_values)

    def test_reserve_not_in_prepared_feed_source_pool(self):
        normal = self._pool()
        reserve = self._pool(reserve=True)
        f = PreparedFeedForm()
        pool_pks = list(f.fields["source_pool"].queryset.values_list("pk", flat=True))
        self.assertNotIn(reserve.pk, pool_pks)
        self.assertIn(normal.pk, pool_pks)


class RatioSectionVisibilityTests(TestCase):
    """A3: the advanced section wrapper hides for non-formula types."""

    def setUp(self):
        self.user = User.objects.create_superuser("vis", "v@e.st", "pw")

    def test_toggle_script_targets_details_wrapper(self):
        self.client.force_login(self.user)
        resp = self.client.get("/products/add/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        # The toggle script must hide the whole advanced-fields section,
        # not only the inner rows.
        self.assertIn("details.advanced-fields", html)
        self.assertIn('section.style.display = isFormula ? "" : "none"', html)


class BurnContrastTests(TestCase):
    """A4: alert rows must not render the Burn cell as text-muted."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser("burn", "b@e.st", "pw")
        cls.child = Child.objects.create(
            first_name="B",
            last_name="C",
            birth_date=timezone.localdate() - timedelta(days=90),
        )
        cls.pl = ProductLine.objects.create(
            item_type="diapers", brand="BurnBrand", line=""
        )

    def test_alert_rows_drop_text_muted_on_burn_cell(self):
        from core.models import SupplyItem, DiaperChange

        SupplyItem.objects.create(
            product_line=self.pl,
            child=None,
            size="1",
            quantity=3,
            initial_quantity=3,
        )
        # 7 changes in the last week → alert row.
        for i in range(7):
            DiaperChange.objects.create(
                child=self.child,
                time=timezone.now() - timedelta(days=i),
                wet=True,
                solid=False,
                diaper_size="1",
            )
        self.client.force_login(self.user)
        resp = self.client.get(f"/children/{self.child.slug}/dashboard/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        import re as _re

        m = _re.search(
            r"Diaper Stock Alerts.*?<tbody>(.*?)</tbody>", html, _re.S
        )
        self.assertIsNotNone(m, "Stock Alerts card not rendered")
        # Find the alert row (table-danger/table-warning) and verify its
        # Burn cell does NOT carry text-muted.
        row_m = _re.search(
            r'<tr[^>]*class="(table-danger|table-warning)"[^>]*>(.*?)</tr>',
            m.group(1),
            _re.S,
        )
        self.assertIsNotNone(row_m, "no alert row rendered")
        burn_m = _re.search(
            r'<td class="text-end([^"]*)">(.*?)</td>', row_m.group(2), _re.S
        )
        self.assertIsNotNone(burn_m, "no burn cell rendered")
        self.assertNotIn("text-muted", burn_m.group(1))

