from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from core.forms import BottleFeedingForm, FeedingForm, PumpingForm
from core.models import Child, FeedInventory, Pumping

User = get_user_model()


def _child():
    return Child.objects.create(
        first_name="W3", birth_date=timezone.now() - timedelta(days=30)
    )


class MarkWarmedTests(TestCase):
    """B2: one-way Mark warmed action."""

    def _unit(self):
        child = _child()
        return FeedInventory.objects.create(
            child=child,
            type="breast_milk",
            amount=100,
            amount_unit="ml",
            amount_remaining=100,
            storage_location="fridge",
            status="fresh",
        )

    def test_mark_warmed_sets_flag_and_ledger(self):
        unit = self._unit()
        user = User.objects.create_user("warmer")
        when = timezone.now()
        unit.mark_warmed(warmed_at=when, user=user)
        unit.refresh_from_db()
        self.assertEqual(unit.warmed_at, when)
        events = list(unit.events.filter(type="warmed"))
        self.assertTrue(events)

    def test_mark_warmed_twice_raises(self):
        unit = self._unit()
        unit.mark_warmed(warmed_at=timezone.now())
        with self.assertRaises(ValidationError):
            unit.mark_warmed(warmed_at=timezone.now())

    def test_warmed_unit_cannot_return_to_cold(self):
        unit = self._unit()
        unit.mark_warmed(warmed_at=timezone.now())
        unit.storage_location = "freezer"
        with self.assertRaises(ValidationError):
            unit.clean()

    def test_view_renders_and_posts(self):
        unit = self._unit()
        admin = User.objects.create_superuser("wadmin", "w@e.st", "pw")
        self.client.force_login(admin)
        url = reverse("core:feedinventory-warm", args=[unit.pk])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        when = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
        resp = self.client.post(url, {"warmed_at": when, "note": ""}, follow=True)
        unit.refresh_from_db()
        self.assertIsNotNone(unit.warmed_at)

    def test_list_button_disabled_when_warmed(self):
        unit = self._unit()
        admin = User.objects.create_superuser("ladmin", "l@e.st", "pw")
        self.client.force_login(admin)
        unit.mark_warmed(warmed_at=timezone.now())
        resp = self.client.get(reverse("core:feedinventory-list"))
        html = resp.content.decode()
        self.assertIn("disabled", html)


class BrandDropdownRemovedTests(TestCase):
    """B7: formula_product dropdown gone from both feeding forms."""

    def test_bottle_form_has_no_formula_product(self):
        f = BottleFeedingForm()
        self.assertNotIn("formula_product", f.fields)
        self.assertIn("formula_source", f.fields)

    def test_feeding_form_has_no_formula_product(self):
        f = FeedingForm()
        self.assertNotIn("formula_product", f.fields)

    def test_milk_inventory_label_renamed(self):
        f = BottleFeedingForm()
        self.assertEqual(
            str(f.fields["feed_inventory"].label), "Milk inventory item"
        )


class QuickAddButtonsTests(TestCase):
    """Feedings page quick-add buttons present."""

    def test_feeding_list_has_quick_adds(self):
        admin = User.objects.create_superuser("qadmin", "q@e.st", "pw")
        self.client.force_login(admin)
        resp = self.client.get(reverse("core:feeding-list"))
        html = resp.content.decode()
        self.assertIn("Add Bottle Feeding", html)
        self.assertIn("Add Breast Feeding", html)
        self.assertIn("Add Solid Feeding", html)


class PumpingMethodDefaultTests(TestCase):
    """Site setting pre-selects the pumping method on add."""

    def test_blank_default_leaves_unselected(self):
        f = PumpingForm()
        self.assertEqual(f.fields["method"].initial, "")

    def test_setting_preselects(self):
        from dbsettings.loading import set_setting_value

        set_setting_value("core.models", "Pumping", "default_method", "electric pump")
        f = PumpingForm()
        self.assertEqual(f.fields["method"].initial, "electric pump")
