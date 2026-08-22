from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class SuppliesNavTestCase(TestCase):
    """#57: Supplies dropdown structure — correct routes, labels, perms."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="navTester", password="testing", is_superuser=True
        )

    def _nav_html(self):
        self.client.force_login(self.user)
        resp = self.client.get("/feedings/")
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_prepared_feed_entries_present(self):
        html = self._nav_html()
        self.assertIn("/prepared-feeds/", html)
        self.assertIn("Prepared Feed", html)
        self.assertIn("Prepared feed entry", html)

    def test_formula_stock_add_entry(self):
        html = self._nav_html()
        self.assertIn("/formula-stock/add/", html)
        self.assertIn("Formula stock entry", html)

    def test_milk_inventory_entry_label(self):
        html = self._nav_html()
        self.assertIn("Milk inventory entry", html)

    def test_order_milk_before_formula_before_prepared(self):
        html = self._nav_html()
        i_milk = html.index("Milk Inventory")
        i_milk_add = html.index("Milk inventory entry")
        i_fs = html.index("Formula Stock")
        i_fs_add = html.index("Formula stock entry")
        i_pf = html.index("Prepared Feed")
        i_pf_add = html.index("Prepared feed entry")
        self.assertLess(i_milk, i_milk_add)
        self.assertLess(i_milk_add, i_fs)
        self.assertLess(i_fs, i_fs_add)
        self.assertLess(i_fs_add, i_pf)
        self.assertLess(i_pf, i_pf_add)

    def test_no_stale_inventory_entry_label_under_formula(self):
        html = self._nav_html()
        # The old mislabeled entry pointed feedinventory-add at Formula
        # Stock position; new nav has no bare "Inventory entry" between
        # Formula Stock and Prepared Feed.
        fs_pos = html.index("Formula Stock")
        pf_pos = html.index("Prepared Feed")
        between = html[fs_pos:pf_pos]
        self.assertNotIn("Inventory entry", between)
