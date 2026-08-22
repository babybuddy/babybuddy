"""Household-timezone derivation tests (issue #36).

The timezone a user picks in Settings must govern day-derived values
(inventory labels, use-by badge clocks) everywhere — not just web
requests, where UserTimezoneMiddleware activates it. Non-web paths
(sync shell, management commands, token-auth API) run under the server
default (UTC), so derivation must read the setting directly.
"""
import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from babybuddy.models import Settings
from core.models import Child, FormulaStock, FeedInventory, ProductLine, Pumping
from core.utils import household_timezone, to_household

NY = ZoneInfo("America/New_York")
UTC = ZoneInfo("UTC")


def aware(y, mo, d, h, mi, tz=UTC):
    return datetime.datetime(y, mo, d, h, mi, tzinfo=tz)


class HouseholdTimezoneHelperTests(TestCase):
    """Resolution rules for household_timezone()."""

    def test_single_user_wins(self):
        user = User.objects.create_user("solo", password="x")
        user.settings.timezone = "America/New_York"
        user.settings.save()
        self.assertEqual(household_timezone(), NY)

    def test_inactive_and_invalid_skipped(self):
        """Inactive users and invalid zone names don't participate."""
        u1 = User.objects.create_user("human", password="x")
        u1.settings.timezone = "America/New_York"
        u1.settings.save()
        u2 = User.objects.create_user("stale", password="x")
        u2.is_active = False
        u2.save()
        u2.settings.timezone = "Mars/Olympus"
        u2.settings.save()
        u3 = User.objects.create_user("ghost", password="x")
        u3.is_active = False
        u3.save()
        u3.settings.timezone = "America/Los_Angeles"
        u3.settings.save()
        self.assertEqual(household_timezone(), NY)

    def test_disagreement_oldest_active_superuser_wins(self):
        """Multiple zones among active users -> the oldest active
        superuser (by pk) decides, not the server default."""
        founder = User.objects.create_superuser("founder", None, "x")
        founder.settings.timezone = "America/New_York"
        founder.settings.save()
        u2 = User.objects.create_user("later", password="x")
        u2.settings.timezone = "America/Los_Angeles"
        u2.settings.save()
        self.assertEqual(household_timezone(), NY)

    def test_no_users_falls_back_to_settings(self):
        self.assertEqual(household_timezone(), ZoneInfo("UTC"))


class LabelTimezoneTests(TestCase):
    """_next_label must derive the day in the household tz, not the
    ambient one (UTC in shells / sync / token-auth API)."""

    @classmethod
    def setUpTestData(cls):
        cls.child = Child.objects.create(
            first_name="TZ", birth_date="2026-05-25"
        )
        cls.user = User.objects.create_user("tztest", password="x")
        cls.user.settings.timezone = "America/New_York"
        cls.user.settings.save()

    def _pump(self, at):
        return Pumping.objects.create(
            child=self.child,
            amount=130,
            amount_unit="ml",
            start=at,
            end=at,
        )

    def test_label_evening_edt_uses_edt_day(self):
        # 02:00 UTC Aug 13 == 10:00 PM EDT Aug 12 -> 260812-01
        pump = self._pump(aware(2026, 8, 13, 2, 0))
        unit = pump.source_inventory.get()
        self.assertEqual(unit.label, "260812-01")

    def test_label_instant_based_ambient_independent(self):
        # Same instant as above, expressed in EDT wall time; the label
        # must be identical (instant-based, ambient-tz independent).
        pump = self._pump(aware(2026, 8, 12, 22, 0, tz=NY))
        unit = pump.source_inventory.get()
        self.assertEqual(unit.label, "260812-01")

    def test_label_seq_increments_within_day(self):
        self._pump(aware(2026, 8, 13, 2, 0))   # Aug 12 EDT evening
        pump2 = self._pump(aware(2026, 8, 13, 6, 0))  # Aug 13 EDT 2 AM
        unit1 = Pumping.objects.order_by("pk").first().source_inventory.get()
        unit2 = pump2.source_inventory.get()
        self.assertEqual(unit1.label, "260812-01")
        self.assertEqual(unit2.label, "260813-01")

    def test_label_seq_increments_same_edt_evening(self):
        # Two pumps in the same UTC/EDT-day divergence window: both are
        # Aug 12 EDT evening -> seq 01 then 02.
        self._pump(aware(2026, 8, 13, 2, 0))   # 10:00 PM EDT Aug 12
        pump2 = self._pump(aware(2026, 8, 13, 2, 30))  # 10:30 PM EDT
        unit2 = pump2.source_inventory.get()
        self.assertEqual(unit2.label, "260812-02")

    def test_manual_unit_creation_uses_household_tz(self):
        # Non-web path simulation: FeedInventory.objects.create in a
        # shell (ambient UTC) — label still EDT-day.
        FeedInventory.objects.create(
            child=self.child,
            type="breast_milk",
            amount=80,
            amount_unit="ml",
            storage_location="fridge",
            expressed_at=aware(2026, 8, 13, 2, 0),
        )
        last = FeedInventory.objects.order_by("pk").last()
        self.assertEqual(last.label, "260812-01")


class UseByTimezoneTests(TestCase):
    """use_by_info() display datetimes must be localized to the
    household tz; window math itself is tz-safe and unchanged."""

    @classmethod
    def setUpTestData(cls):
        cls.child = Child.objects.create(
            first_name="TZ", birth_date="2026-05-25"
        )
        cls.user = User.objects.create_user("tztest2", password="x")
        cls.user.settings.timezone = "America/New_York"
        cls.user.settings.save()

    def _unit(self, expressed_at, storage="fridge"):
        return FeedInventory.objects.create(
            child=self.child,
            type="breast_milk",
            amount=100,
            amount_unit="ml",
            storage_location=storage,
            expressed_at=expressed_at,
        )

    def test_two_tier_bounds_localized(self):
        # 02:00 UTC Aug 13 == 10:00 PM EDT Aug 12. Fridge two-tier:
        # optimal +4d, acceptable +8d — both must come back in NY tz.
        unit = self._unit(aware(2026, 8, 13, 2, 0))
        info = unit.use_by_info()
        self.assertEqual(info["tier"], "two_tier")
        self.assertEqual(info["optimal_at"].tzinfo, NY)
        self.assertEqual(info["acceptable_at"].tzinfo, NY)
        # Sanity: the instants are unchanged (4d/8d after expression).
        self.assertEqual(
            info["optimal_at"],
            aware(2026, 8, 12, 22, 0, tz=NY) + timezone.timedelta(days=4),
        )
        self.assertEqual(
            info["acceptable_at"],
            aware(2026, 8, 12, 22, 0, tz=NY) + timezone.timedelta(days=8),
        )

    def test_single_tier_bound_localized(self):
        # Cooler: single hard bound cooler_entered_at + 24h. Entered
        # 02:00 UTC Aug 13 (10:00 PM EDT Aug 12) -> bound Aug 14 02:00
        # UTC == Aug 13 10:00 PM EDT.
        unit = FeedInventory.objects.create(
            child=self.child,
            type="breast_milk",
            amount=100,
            amount_unit="ml",
            storage_location="cooler",
            expressed_at=aware(2026, 8, 13, 2, 0),
            cooler_entered_at=aware(2026, 8, 13, 2, 0),
        )
        info = unit.use_by_info()
        self.assertEqual(info["tier"], "single")
        self.assertEqual(info["bound_at"].tzinfo, NY)
        self.assertEqual(
            info["bound_at"], aware(2026, 8, 13, 22, 0, tz=NY)
        )

    def test_tooltip_renders_edt_wall_time(self):
        # The original bug: tooltip strftime'd raw UTC datetimes, so a
        # 10 PM EDT bound printed as "Aug 14 02:00" (UTC). Must print
        # the household wall clock. now pinned inside the window so
        # the tooltip renders the bound, not the discard branch.
        unit = FeedInventory.objects.create(
            child=self.child,
            type="breast_milk",
            amount=100,
            amount_unit="ml",
            storage_location="cooler",
            expressed_at=aware(2026, 8, 13, 2, 0),
            cooler_entered_at=aware(2026, 8, 13, 2, 0),
        )
        tooltip = unit.use_by_tooltip(now=aware(2026, 8, 13, 3, 0))
        self.assertIn("Aug 13 22:00", tooltip)
        self.assertNotIn("02:00", tooltip)

    def test_tooltip_two_tier_renders_edt_wall_time(self):
        unit = self._unit(aware(2026, 8, 13, 2, 0), storage="fridge")
        # Pin now INSIDE the window (CI 5849, 2026-08-21): an unpinned
        # call aged past the +8d acceptable bound and flipped the
        # tooltip to the discard branch.
        tooltip = unit.use_by_tooltip(now=aware(2026, 8, 14, 3, 0))
        self.assertIn("Aug 16 22:00", tooltip)  # optimal: Aug 12 EDT + 4d
        self.assertNotIn("06:00", tooltip)      # UTC artifacts gone

    def test_formula_stock_bound_localized(self):
        # FormulaStock.use_by_info mirrors FeedInventory — same rule.
        # Opened 1h ago (now-relative: its tooltip property takes no
        # now=, and an expired bound renders the discard branch).
        opened = timezone.now() - timezone.timedelta(hours=1)
        pl = ProductLine.objects.create(
            item_type="formula", brand="Test", line=""
        )
        stock = FormulaStock.objects.create(
            product_line=pl,
            form="rtf",
            container_size=59,
            quantity=1,
            opened_at=opened,
        )
        info = stock.use_by_info()
        self.assertEqual(info["bound_at"].tzinfo, NY)
        # opened + 48h, household wall clock
        expected = to_household(opened + timezone.timedelta(hours=48))
        self.assertEqual(info["bound_at"], expected)
        # Tooltip shows the same EDT wall time (bug: printed UTC).
        # NB: FormulaStock.use_by_tooltip is a property.
        self.assertIn(expected.strftime("%b %d %H:%M"), stock.use_by_tooltip)


class DoctorVisitStrTests(TestCase):
    """__str__ must render the household-local date, not UTC date."""

    def test_str_uses_household_date(self):
        from core.models import DoctorVisit

        user = User.objects.create_user("tztest3", password="x")
        user.settings.timezone = "America/New_York"
        user.settings.save()
        visit = DoctorVisit.objects.create(
            child=Child.objects.create(
                first_name="TZ", birth_date="2026-05-25"
            ),
            date_time=aware(2026, 8, 13, 1, 30),  # 9:30 PM EDT Aug 12
        )
        self.assertIn("2026-08-12", str(visit))
        self.assertNotIn("2026-08-13", str(visit))
