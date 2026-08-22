from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from core.models import SupplyItem, ProductLine, Child


class SupplyItemIdentifierTests(TestCase):
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

    def test_str_includes_pool_number(self):
        pool = SupplyItem.objects.create(
            child=self.child, product_line=self.pl, size="NB", quantity=2
        )
        s = str(pool)
        self.assertIn("[NB]", s)
        self.assertIn(f"(#{pool.id})", s)

    def test_list_page_shows_pool_id_column(self):
        pool = SupplyItem.objects.create(
            child=self.child, product_line=self.pl, size="NB", quantity=2
        )
        c = Client()
        c.force_login(self.user)
        resp = c.get(reverse("core:supplyitem-list"))
        self.assertEqual(resp.status_code, 200)
        html = resp.content.decode()
        self.assertIn("text-muted font-monospace", html)
        self.assertIn(f"<td class=\"text-muted font-monospace\">{pool.id}</td>", html)
