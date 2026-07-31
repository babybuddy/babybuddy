from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core import models


@override_settings(USE_TZ=True, TIME_ZONE="Europe/Madrid")
class FoodAPIBase(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="food-api-admin",
            password="test",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_login(self.user)
        self.child = models.Child.objects.create(
            first_name="Lucía",
            birth_date=timezone.localdate() - timezone.timedelta(days=365),
        )
        self.banana = models.Food.objects.get(name="Plátano")
        self.oats = models.Food.objects.get(name="Avena")


class FoodAPITestCase(FoodAPIBase):
    endpoint = reverse("api:food-list")

    def test_list_filter_and_create_food(self):
        response = self.client.get(self.endpoint, {"category": "fruit"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Plátano", [item["name"] for item in response.data["results"]])

        response = self.client.post(
            self.endpoint,
            {"name": "  Alimento de API  ", "category": "vegetable"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "Alimento de API")

    def test_rejects_case_insensitive_duplicate(self):
        response = self.client.post(
            self.endpoint,
            {"name": " plátano ", "category": "fruit"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_used_food_must_be_deactivated_instead_of_deleted(self):
        meal = models.Meal.objects.create(
            child=self.child,
            time=timezone.now(),
            meal_type="breakfast",
        )
        meal.foods.add(self.banana)
        response = self.client.delete(
            reverse("api:food-detail", args=[self.banana.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(models.Food.objects.filter(pk=self.banana.pk).exists())


class MealAPITestCase(FoodAPIBase):
    endpoint = reverse("api:meal-list")

    def meal_data(self, **overrides):
        data = {
            "child": self.child.pk,
            "time": timezone.now().isoformat(),
            "meal_type": "breakfast",
            "foods": [self.banana.pk, self.oats.pk],
            "quantity": "normal",
            "preparation": "pieces",
            "notes": "Datos ficticios",
            "tags": ["favorita", "alimento nuevo"],
        }
        data.update(overrides)
        return data

    def test_create_read_and_filter_meal_with_foods_and_tags(self):
        response = self.client.post(self.endpoint, self.meal_data(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        meal = models.Meal.objects.get(pk=response.data["id"])
        self.assertCountEqual(meal.foods.values_list("id", flat=True), [self.banana.pk, self.oats.pk])
        self.assertCountEqual(meal.tags.names(), ["favorita", "alimento nuevo"])

        response = self.client.get(self.endpoint, {"food": self.banana.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_rejects_empty_or_inactive_new_foods(self):
        response = self.client.post(self.endpoint, self.meal_data(foods=[]), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        inactive = models.Food.objects.get(name="Yogur")
        inactive.active = False
        inactive.save()
        response = self.client.post(
            self.endpoint,
            self.meal_data(foods=[inactive.pk]),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_keeps_an_existing_inactive_food(self):
        self.banana.active = False
        self.banana.save()
        meal = models.Meal.objects.create(
            child=self.child,
            time=timezone.now(),
            meal_type="breakfast",
        )
        meal.foods.add(self.banana)
        response = self.client.patch(
            reverse("api:meal-detail", args=[meal.pk]),
            {"foods": [self.banana.pk, self.oats.pk]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)


class ChildFoodProfileAPITestCase(FoodAPIBase):
    endpoint = reverse("api:childfoodprofile-list")

    def test_create_and_filter_profile(self):
        response = self.client.post(
            self.endpoint,
            {
                "child": self.child.pk,
                "food": self.banana.pk,
                "taste": "likes very much",
                "tolerance": "well tolerated",
                "notes": "Sin incidencias",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn("updated", response.data)
        response = self.client.get(self.endpoint, {"child": self.child.pk, "category": "fruit"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)


class FoodAPIPermissionTestCase(APITestCase):
    def test_model_permissions_are_applied(self):
        user = get_user_model().objects.create_user(username="reader", password="test")
        user.user_permissions.add(Permission.objects.get(codename="view_food"))
        self.client.force_login(user)
        endpoint = reverse("api:food-list")
        self.assertEqual(self.client.get(endpoint).status_code, status.HTTP_200_OK)
        response = self.client.post(endpoint, {"name": "Pera", "category": "fruit"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
