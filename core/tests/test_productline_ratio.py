from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.forms import FormulaStockForm, ProductLineForm
from core.models import ProductLine

User = get_user_model()


class ProductLineRatioFieldTests(TestCase):
    """#58: ratio fields settable in the UI, pair-validated, formula-gated."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="ratioTester", password="testing", is_superuser=True
        )

    def test_form_exposes_ratio_fields(self):
        form = ProductLineForm()
        self.assertIn("scoop_grams", form.fields)
        self.assertIn("water_per_scoop_ml", form.fields)

    def test_pair_validation_both_or_neither(self):
        data = {
            "item_type": "formula",
            "brand": "Similac",
            "line": "360 Total Care",
            "scoop_grams": "8.7",
            "water_per_scoop_ml": "60",
        }
        form = ProductLineForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        line = form.save()
        self.assertEqual(line.scoop_grams, 8.7)
        self.assertEqual(line.water_per_scoop_ml, 60.0)

        data["water_per_scoop_ml"] = ""
        form = ProductLineForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("scoop_grams", form.errors)

    def test_zero_and_negative_rejected(self):
        for vals in ([0, 60], [8.7, 0], [-1, 60], [8.7, -5]):
            data = {
                "item_type": "formula",
                "brand": "B",
                "line": "",
                "scoop_grams": str(vals[0]),
                "water_per_scoop_ml": str(vals[1]),
            }
            form = ProductLineForm(data=data)
            self.assertFalse(form.is_valid(), f"expected invalid for {vals}")

    def test_blank_ratio_still_valid(self):
        data = {
            "item_type": "formula",
            "brand": "Enfamil",
            "line": "",
            "scoop_grams": "",
            "water_per_scoop_ml": "",
        }
        form = ProductLineForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)
        line = form.save()
        self.assertIsNone(line.scoop_grams)
        self.assertIsNone(line.water_per_scoop_ml)

    def test_add_page_renders_with_ratio_fields(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse("core:productline-add"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("id_scoop_grams", html)
        self.assertIn("id_water_per_scoop_ml", html)
        self.assertIn("Formula Mixing Ratio", html)

    def test_edit_page_retroactive_ratio(self):
        line = ProductLine.objects.create(
            item_type="formula", brand="Similac", line="360 Total Care"
        )
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse("core:productline-update", args=[line.pk]),
            {
                "item_type": "formula",
                "brand": "Similac",
                "line": "360 Total Care",
    "scoop_grams": "8.7",
                "water_per_scoop_ml": "60",
            },
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        line.refresh_from_db()
        self.assertEqual(line.scoop_grams, 8.7)
        self.assertEqual(line.water_per_scoop_ml, 60.0)

    def test_rtf_stock_still_blocked_on_ratio_line(self):
        # B4 (2026-08-21): one product line may host BOTH a powder pool
        # and an RTF pool — ratio fields are powder-only facts and are
        # ignored for ready-to-feed pools. The old refusal is gone.
        line = ProductLine.objects.create(
            item_type="formula",
            brand="RTF Brand",
            line="",
            scoop_grams=8.7,
            water_per_scoop_ml=60,
        )
        stock = FormulaStockForm(
            data={
                "product_line": line.pk,
                "form": "rtf",
                "container_size": "59",
                "quantity": "1",
                "drain_priority": "0",
            }
        )
        self.assertTrue(stock.is_valid(), msg=str(stock.errors))

