from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from core.forms import FormulaStockForm, PreparedFeedForm
from core.models import Child, FormulaStock, ProductLine

User = get_user_model()


def _line(ratio=False, brand="WaveBrand"):
    return ProductLine.objects.create(
        item_type="formula",
        brand=brand,
        line="",
        scoop_grams=8.7 if ratio else None,
        water_per_scoop_ml=60 if ratio else None,
    )


class RTFOnRatioLineTests(TestCase):
    """B4: one product line, both pool forms."""

    def test_rtf_pool_allowed_on_ratio_line(self):
        line = _line(ratio=True)
        f = FormulaStockForm(
            data={
                "product_line": line.pk,
                "form": "rtf",
                "container_size": 2000,
                "quantity": 2,
                "drain_priority": 0,
            }
        )
        self.assertTrue(
            f.is_valid(), msg=str(f.errors)
        )


class OpenedAtAddTests(TestCase):
    """B3: 'Already opened?' block on the add form."""

    def test_opened_row_locks_quantity_and_requires_grams(self):
        line = _line()
        f = FormulaStockForm(
            data={
                "product_line": line.pk,
                "form": "powder",
                "container_size": 400,
                "quantity": 3,
                "drain_priority": 0,
                "opened_at": timezone.now(),
                # grams_remaining intentionally blank
            }
        )
        self.assertFalse(f.is_valid())
        self.assertIn("grams_remaining", f.errors)

    def test_opened_rtf_requires_ml_and_clears_grams(self):
        line = _line()
        f = FormulaStockForm(
            data={
                "product_line": line.pk,
                "form": "rtf",
                "container_size": 2000,
                "quantity": 1,
                "opened_at": timezone.now(),
                "grams_remaining": 500,  # wrong field for RTF — gets cleared
                "ml_remaining": 1500,
                "drain_priority": 0,
            }
        )
        self.assertTrue(f.is_valid(), msg=str(f.errors))
        self.assertEqual(f.cleaned_data["ml_remaining"], 1500)
        self.assertIsNone(f.cleaned_data["grams_remaining"])
        self.assertEqual(f.cleaned_data["quantity"], 1)

    def test_form_renders_opened_block(self):
        User.objects.create_superuser("render", "r@e.st", "pw")
        from django.test import Client

        c = Client()
        c.force_login(User.objects.get(username="render"))
        resp = c.get("/formula-stock/add/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Already opened?", html)
        self.assertIn("id_opened_at", html)


class ClockOverrideTests(TestCase):
    """C4: opened-container clocks are site settings."""

    def _opened_rtf(self):
        line = _line(brand="ClockRTF")
        return FormulaStock.objects.create(
            product_line=line,
            form="rtf",
            container_size=2000,
            quantity=1,
            opened_at=timezone.now(),
            ml_remaining=1500,
        )

    def _opened_powder(self):
        line = _line(brand="ClockPowder")
        return FormulaStock.objects.create(
            product_line=line,
            form="powder",
            container_size=400,
            quantity=1,
            opened_at=timezone.now(),
            grams_remaining=380,
        )

    def test_defaults_48h_and_31d(self):
        rtf = self._opened_rtf()
        powder = self._opened_powder()
        self.assertAlmostEqual(
            (rtf.use_by() - rtf.opened_at).total_seconds() / 3600, 48, places=0
        )
        self.assertAlmostEqual(
            (powder.use_by() - powder.opened_at).total_seconds() / 86400,
            31,
            places=0,
        )

    def test_rtf_clock_overridable(self):
        from dbsettings.loading import set_setting_value

        set_setting_value(
            "core.models", "FormulaStock", "rtf_use_by_hours", 24
        )
        rtf = self._opened_rtf()
        self.assertAlmostEqual(
            (rtf.use_by() - rtf.opened_at).total_seconds() / 3600,
            24,
            places=0,
        )

    def test_powder_clock_overridable(self):
        from dbsettings.loading import set_setting_value

        set_setting_value(
            "core.models", "FormulaStock", "powder_use_by_days", 14
        )
        powder = self._opened_powder()
        self.assertAlmostEqual(
            (powder.use_by() - powder.opened_at).total_seconds() / 86400,
            14,
        places=0,
        )


class PreparedFormHelpTextTests(TestCase):
    """B6: help text + placeholder present in rendered form."""

    def test_grams_used_help_and_placeholder(self):
        User.objects.create_superuser("help", "h@e.st", "pw")
        from django.test import Client

        c = Client()
        c.force_login(User.objects.get(username="help"))
        resp = c.get("/prepared-feeds/add/")
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("Auto-computed from the product&#x27;s mixing ratio", html)
        self.assertIn("Auto-calculated on save from the mixing ratio", html)
        self.assertIn("room-temperature bottle", html)


class ReserveExcludedAlreadyShipped(TestCase):
    """Wave-1 A2 parity: prepared-feed source_pool still excludes reserves."""

    def test_source_pool_excludes_reserve(self):
        line = _line(brand="ReserveBrand")
        normal = FormulaStock.objects.create(
            product_line=line,
            form="powder",
            container_size=400,
            quantity=1,
            opened_at=timezone.now(),
            grams_remaining=300,
        )
        reserve = FormulaStock.objects.create(
            product_line=line,
            form="powder",
            container_size=400,
            quantity=1,
            opened_at=timezone.now(),
            grams_remaining=300,
            is_reserve=True,
        )
        f = PreparedFeedForm()
        pks = list(f.fields["source_pool"].queryset.values_list("pk", flat=True))
        self.assertIn(normal.pk, pks)
        self.assertNotIn(reserve.pk, pks)
