from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.translation import override

from core import forms, models


@override_settings(LANGUAGE_CODE="es")
class FoodCatalogTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="food-user",
            password="password",
        )
        cls.user.settings.language = "es"
        cls.user.settings.save(update_fields=["language"])
        cls.food = models.Food.objects.get(name="Plátano")
        cls.food.notes = "Alimento habitual"
        cls.food.save(update_fields=["notes"])
        cls.inactive_food = models.Food.objects.get(name="Yogur")
        cls.inactive_food.active = False
        cls.inactive_food.save(update_fields=["active"])

    def setUp(self):
        self.client.force_login(self.user)

    def grant(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label="core",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    def test_food_form_strips_name_and_rejects_case_insensitive_duplicate(self):
        form = forms.FoodForm(
            data={
                "name": "  Fruta de prueba  ",
                "category": "fruit",
                "active": True,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["name"], "Fruta de prueba")

        with override("es"):
            duplicate = forms.FoodForm(
                data={
                    "name": "  PLÁTANO ",
                    "category": "fruit",
                    "active": True,
                }
            )
            self.assertFalse(duplicate.is_valid())
            self.assertIn(
                "Ya existe un alimento con este nombre.",
                duplicate.errors["name"],
            )

    def test_view_permission_allows_list_but_not_changes(self):
        self.grant("view_food")

        response = self.client.get(
            reverse("core:food-list"),
            {"name": "Plátano", "filtered": "1"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plátano")
        self.assertNotContains(response, reverse("core:food-add"))
        self.assertNotContains(response, reverse("core:food-update", args=[self.food.pk]))

        self.assertEqual(
            self.client.get(reverse("core:food-add")).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("core:food-update", args=[self.food.pk])
            ).status_code,
            403,
        )

    def test_food_can_be_added_and_updated_with_permissions(self):
        self.grant("view_food", "add_food", "change_food")

        response = self.client.post(
            reverse("core:food-add"),
            {
                "name": "  Cereal de prueba ",
                "category": "cereal",
                "active": True,
                "notes": "Para el desayuno",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        food = models.Food.objects.get(name="Cereal de prueba")
        self.assertTrue(food.active)

        response = self.client.post(
            reverse("core:food-update", args=[food.pk]),
            {
                "name": food.name,
                "category": food.category,
                "notes": food.notes,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        food.refresh_from_db()
        self.assertFalse(food.active)
        self.assertContains(response, "Inactivo")

    def test_list_filters_by_name_category_and_active_status(self):
        self.grant("view_food")

        response = self.client.get(
            reverse("core:food-list"),
            {
                "name": "plá",
                "category": "fruit",
                "active": "true",
                "filtered": "1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plátano")
        self.assertNotContains(response, "Yogur")

    def test_navigation_and_pages_are_in_spanish(self):
        self.grant("view_food", "add_food", "change_food")

        with override("es"):
            response = self.client.get(reverse("core:food-list"))
            self.assertContains(response, "Catálogo de alimentos")
            self.assertContains(response, "Añadir alimento")
            self.assertContains(response, "Fruta")

            response = self.client.get(
                reverse("core:food-list"),
                {"active": "false", "filtered": "1"},
            )
            self.assertContains(response, "Inactivo")

            response = self.client.get(reverse("core:food-add"))
            self.assertContains(response, "Añadir alimento")
            self.assertContains(response, "Categoría")

    def test_catalog_has_no_delete_route(self):
        with self.assertRaises(NoReverseMatch):
            reverse("core:food-delete", args=[self.food.pk])

    def test_deactivation_keeps_existing_meal_history(self):
        child = models.Child.objects.create(
            first_name="Ana",
            birth_date=timezone.localdate(),
        )
        meal = models.Meal.objects.create(
            child=child,
            time=timezone.localtime() - timezone.timedelta(hours=1),
            meal_type="breakfast",
        )
        meal.foods.add(self.food)

        self.food.active = False
        self.food.save()

        self.assertTrue(meal.foods.filter(pk=self.food.pk).exists())
