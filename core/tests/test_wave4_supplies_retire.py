import importlib
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.models import Child, DiaperChange, ProductLine, Pumping, SupplyItem

User = get_user_model()


def _child():
    return Child.objects.create(
        first_name="W4", birth_date=timezone.now() - timedelta(days=30)
    )


def _diaper_line(brand="TestBrand"):
    return ProductLine.objects.create(item_type="diapers", brand=brand, line="")


def _wipes_line(brand="WipeCo"):
    return ProductLine.objects.create(item_type="wipes", brand=brand, line="")


# NOTE: MilkItemTypeRemovedTests (verifying the 0074 data-migration's
# milk-line cleanup) is intentionally absent in the squashed upstream
# delivery: upstream databases never contained fork-only "milk" item
# types, so the deleted-migration's RunPython is a guaranteed no-op
# there. The test remains meaningful only on the fork's own chain.

class SupplyItemRetireTests(TestCase):
    """Retire/un-retire: hidden from FIFO decrement, flag flips via view."""

    def _setup_pools(self):
        child = _child()
        line = _diaper_line()
        # Active pool: NEWER eligibility (loses FIFO to the retired one)
        active = SupplyItem.objects.create(
            product_line=line,
            size="3",
            quantity=10,
            usage_eligible=timezone.now() - timedelta(days=1),
        )
        # Retired pool: OLDER eligibility — would win FIFO if not retired
        retired = SupplyItem.objects.create(
            product_line=line,
            size="3",
            quantity=20,
            usage_eligible=timezone.now() - timedelta(days=10),
            is_retired=True,
        )
        return child, active, retired

    def test_retired_excluded_from_fifo(self):
        child, active, retired = self._setup_pools()
        DiaperChange.objects.create(
            child=child,
            time=timezone.now(),
            wet=True,
            solid=False,
            diaper_size="3",
        )
        active.refresh_from_db()
        retired.refresh_from_db()
        self.assertEqual(active.quantity, 9)
        self.assertEqual(retired.quantity, 20)

    def test_retire_view_flips_flag(self):
        child, active, retired = self._setup_pools()
        admin = User.objects.create_superuser("radmin", "r@e.st", "pw")
        self.client.force_login(admin)
        resp = self.client.post(
            reverse("core:supplyitem-retire", args=[active.pk]),
            {"mode": "retire"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        active.refresh_from_db()
        self.assertTrue(active.is_retired)

    def test_unretire_view_restores(self):
        child, active, retired = self._setup_pools()
        admin = User.objects.create_superuser("uadmin", "u@e.st", "pw")
        self.client.force_login(admin)
        resp = self.client.post(
            reverse("core:supplyitem-retire", args=[retired.pk]),
            {"mode": "unretire"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        retired.refresh_from_db()
        self.assertFalse(retired.is_retired)

    def test_retired_counts_as_not_usable_in_burn_table(self):
        child, active, retired = self._setup_pools()
        from core.inventory import compute_diaper_burn_table

        table = compute_diaper_burn_table(child, period_days=7)
        rows = {r["size"]: r for r in table["rows"]}
        self.assertEqual(rows["3"]["usable"], 10)
        self.assertEqual(rows["3"]["on_hand"], 30)


class WipesPageTests(TestCase):
    """Wipes list view filters to wipes item type."""

    def test_wipes_list_only_wipes(self):
        wipes_line = _wipes_line()
        diaper_line = _diaper_line()
        SupplyItem.objects.create(product_line=wipes_line, quantity=5)
        SupplyItem.objects.create(product_line=diaper_line, quantity=10)
        admin = User.objects.create_superuser("wadmin", "w@e.st", "pw")
        self.client.force_login(admin)
        resp = self.client.get(reverse("core:wipes-list"))
        self.assertEqual(resp.status_code, 200)
        pl_ids = [i.product_line_id for i in resp.context["object_list"]]
        self.assertIn(wipes_line.pk, pl_ids)
        self.assertNotIn(diaper_line.pk, pl_ids)

    def test_nav_link_present(self):
        admin = User.objects.create_superuser("nadmin", "n@e.st", "pw")
        self.client.force_login(admin)
        resp = self.client.get(reverse("core:wipes-list"))
        self.assertIn(b"Wipes", resp.content)

    def test_supplies_list_shows_retired_badge(self):
        _child()  # supplies list groups by child — needs one to exist
        line = _diaper_line()
        SupplyItem.objects.create(
            product_line=line, quantity=0, is_retired=True
        )
        admin = User.objects.create_superuser("badmin", "b@e.st", "pw")
        self.client.force_login(admin)
        resp = self.client.get(reverse("core:supplyitem-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Retired", resp.content)
