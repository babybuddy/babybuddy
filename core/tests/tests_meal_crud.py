from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core import forms, models


@override_settings(LANGUAGE_CODE="es")
class MealCrudTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="meal-user",
            password="password",
        )
        cls.user.settings.language = "es"
        cls.user.settings.save(update_fields=["language"])
        cls.child = models.Child.objects.create(
            first_name="Ana",
            last_name="Prueba",
            birth_date=timezone.localdate(),
        )
        cls.banana = models.Food.objects.get(name="Plátano")
        cls.oats = models.Food.objects.get(name="Avena")
        cls.inactive_food = models.Food.objects.get(name="Yogur")
        cls.inactive_food.active = False
        cls.inactive_food.save(update_fields=["active"])
        cls.meal = models.Meal.objects.create(
            child=cls.child,
            time=timezone.localtime() - timezone.timedelta(hours=2),
            meal_type="breakfast",
            quantity="normal",
            preparation="pieces",
            notes="Comió con apetito",
        )
        cls.meal.foods.add(cls.banana, cls.inactive_food)

    def setUp(self):
        self.client.force_login(self.user)

    def grant(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label="core",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    @staticmethod
    def form_time():
        value = timezone.localtime() - timezone.timedelta(hours=1)
        return value.strftime("%Y-%m-%d %H:%M:%S")

    def meal_data(self, **overrides):
        data = {
            "child": self.child.pk,
            "time": self.form_time(),
            "meal_type": "lunch",
            "foods": [self.banana.pk, self.oats.pk],
            "quantity": "little",
            "preparation": "pieces",
            "notes": "Prueba",
        }
        data.update(overrides)
        return data

    def test_new_meal_form_only_offers_active_foods(self):
        form = forms.MealForm()

        self.assertIn(self.banana, form.fields["foods"].queryset)
        self.assertIn(self.oats, form.fields["foods"].queryset)
        self.assertNotIn(self.inactive_food, form.fields["foods"].queryset)

    def test_meal_form_renders_searchable_food_checkboxes(self):
        self.grant("add_meal")

        response = self.client.get(reverse("core:meal-add"))

        self.assertContains(response, "data-food-multicheck")
        self.assertContains(response, "data-food-search")
        self.assertNotContains(response, "data-food-quick-add-open")
        self.assertContains(response, 'search.addEventListener("input"')
        self.assertContains(response, "fs-6")
        self.assertContains(response, "overflow-x: hidden")
        self.assertGreater(
            response.content.decode().count('type="checkbox" name="foods"'),
            1,
        )
        self.assertNotContains(response, '<select name="foods"')
        self.assertNotContains(response, '<details class="food-multicheck')

    def test_recent_foods_are_grouped_independently_for_each_child(self):
        older_meal = models.Meal.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=2),
            meal_type="breakfast",
        )
        older_meal.foods.add(self.oats)
        other_child = models.Child.objects.create(
            first_name="Leo",
            birth_date=timezone.localdate(),
        )
        apple = models.Food.objects.get(name="Manzana")
        other_meal = models.Meal.objects.create(
            child=other_child,
            time=timezone.localtime() - timezone.timedelta(hours=1),
            meal_type="snack",
        )
        other_meal.foods.add(apple)

        form = forms.MealForm(user=self.user)
        recent = form.fields["foods"].widget.recent_by_child

        self.assertIn(self.banana.pk, recent[self.child.pk][:2])
        self.assertIn(self.inactive_food.pk, recent[self.child.pk][:2])
        self.assertEqual(recent[self.child.pk][-1], self.oats.pk)
        self.assertEqual(recent[other_child.pk], [apple.pk])

    def test_quick_food_creation_requires_permission(self):
        response = self.client.post(
            reverse("core:food-quick-add"),
            {"name": "Papaya", "category": "fruit", "active": "on"},
        )

        self.assertEqual(response.status_code, 403)

    def test_authorized_user_can_create_food_from_meal_form(self):
        self.grant("add_meal", "add_food")

        response = self.client.get(reverse("core:meal-add"))
        self.assertContains(response, "data-food-quick-add-open")
        self.assertContains(response, "data-food-recent-badge")
        self.assertContains(response, "Crear alimento sin salir de la comida")
        self.assertContains(response, "Crear y seleccionar")

        response = self.client.post(
            reverse("core:food-quick-add"),
            {"name": "  Papaya  ", "category": "fruit", "active": "on"},
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        food = models.Food.objects.get(pk=payload["id"])
        self.assertEqual(food.name, "Papaya")
        self.assertEqual(food.category, "fruit")
        self.assertTrue(food.active)

        duplicate = self.client.post(
            reverse("core:food-quick-add"),
            {"name": "PAPAYA", "category": "fruit", "active": "on"},
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("name", duplicate.json()["errors"])

    def test_edit_form_marks_existing_foods_in_multicheck(self):
        self.grant("change_meal")

        response = self.client.get(
            reverse("core:meal-update", args=[self.meal.pk])
        )

        content = response.content.decode()
        self.assertRegex(
            content,
            rf'<input[^>]+value="{self.banana.pk}"[^>]+checked>',
        )
        self.assertRegex(
            content,
            rf'<input[^>]+value="{self.inactive_food.pk}"[^>]+checked>',
        )

    def test_edit_form_keeps_selected_inactive_food_available(self):
        other_inactive = models.Food.objects.create(
            name="Alimento inactivo de prueba",
            category="fruit",
            active=False,
        )

        form = forms.MealForm(instance=self.meal)

        self.assertIn(self.inactive_food, form.fields["foods"].queryset)
        self.assertNotIn(other_inactive, form.fields["foods"].queryset)

    def test_meal_requires_at_least_one_food(self):
        form = forms.MealForm(data=self.meal_data(foods=[]))

        self.assertFalse(form.is_valid())
        self.assertIn("foods", form.errors)

    def test_inactive_food_cannot_be_added_to_new_meal(self):
        form = forms.MealForm(
            data=self.meal_data(foods=[self.inactive_food.pk])
        )

        self.assertFalse(form.is_valid())
        self.assertIn("foods", form.errors)

    def test_view_permission_allows_list_but_not_changes(self):
        self.grant("view_meal")

        response = self.client.get(reverse("core:meal-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plátano")
        self.assertNotContains(response, reverse("core:meal-add"))
        self.assertEqual(self.client.get(reverse("core:meal-add")).status_code, 403)
        self.assertEqual(
            self.client.get(
                reverse("core:meal-update", args=[self.meal.pk])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("core:meal-delete", args=[self.meal.pk])
            ).status_code,
            403,
        )

    def test_authorized_user_can_add_meal_with_multiple_foods(self):
        self.grant("view_meal", "add_meal")

        response = self.client.post(
            reverse("core:meal-add"),
            self.meal_data(),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        meal = models.Meal.objects.exclude(pk=self.meal.pk).get()
        self.assertCountEqual(meal.foods.all(), [self.banana, self.oats])
        self.assertEqual(meal.quantity, "little")

    def test_meal_form_shows_and_saves_tags(self):
        self.grant("view_meal", "add_meal")

        response = self.client.get(reverse("core:meal-add"))
        self.assertContains(response, "Etiquetas")
        self.assertContains(response, "babybuddy-tags-editor")

        response = self.client.post(
            reverse("core:meal-add"),
            self.meal_data(tags='favorita,"alimento nuevo"'),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        meal = models.Meal.objects.exclude(pk=self.meal.pk).get()
        self.assertCountEqual(
            meal.tags.values_list("name", flat=True),
            ["favorita", "alimento nuevo"],
        )

    def test_authorized_user_can_edit_meal_and_keep_inactive_food(self):
        self.grant("view_meal", "change_meal")

        response = self.client.post(
            reverse("core:meal-update", args=[self.meal.pk]),
            self.meal_data(
                foods=[self.banana.pk, self.inactive_food.pk],
                quantity="all",
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.meal.refresh_from_db()
        self.assertEqual(self.meal.quantity, "all")
        self.assertCountEqual(
            self.meal.foods.all(),
            [self.banana, self.inactive_food],
        )

    def test_authorized_user_can_delete_meal(self):
        self.grant("view_meal", "delete_meal")

        response = self.client.post(
            reverse("core:meal-delete", args=[self.meal.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(models.Meal.objects.filter(pk=self.meal.pk).exists())
        self.assertTrue(models.Food.objects.filter(pk=self.banana.pk).exists())

    def test_meal_pages_and_navigation_are_in_spanish(self):
        self.grant("view_meal", "add_meal", "change_meal", "delete_meal")

        response = self.client.get(reverse("core:meal-list"))
        self.assertContains(response, "Comidas")
        self.assertContains(response, "Añadir comida")
        self.assertContains(response, "Desayuno")
        self.assertContains(response, "Plátano")
        self.assertContains(response, "Yogur")
        self.assertContains(response, "Cantidad aproximada")

        response = self.client.get(reverse("core:meal-add"))
        self.assertContains(response, "Selecciona uno o varios alimentos.")
        self.assertContains(response, "Tipo de comida")

    def test_meals_can_be_filtered_by_all_supported_fields(self):
        self.meal.tags.add("favorita")
        lunch = models.Meal.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=2),
            meal_type="lunch",
            quantity="little",
        )
        lunch.foods.add(self.oats)
        self.grant("view_meal")

        filters = {
            "food": (self.banana.pk, [self.meal]),
            "category": ("dairy", [self.meal]),
            "meal_type": ("lunch", [lunch]),
            "quantity": ("little", [lunch]),
            "tag": (self.meal.tags.get().pk, [self.meal]),
            "date_from": (
                timezone.localdate().isoformat(),
                [self.meal],
            ),
            "date_to": (
                (timezone.localdate() - timezone.timedelta(days=1)).isoformat(),
                [lunch],
            ),
        }

        for field, (value, expected) in filters.items():
            with self.subTest(field=field):
                response = self.client.get(
                    reverse("core:meal-list"),
                    {field: value, "filtered": "1"},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(list(response.context["object_list"]), expected)

    def test_meals_are_grouped_by_local_date(self):
        older = models.Meal.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=2),
            meal_type="dinner",
        )
        older.foods.add(self.oats)
        self.grant("view_meal")

        response = self.client.get(reverse("core:meal-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content.decode().count('class="table-group-divider"'),
            2,
        )
