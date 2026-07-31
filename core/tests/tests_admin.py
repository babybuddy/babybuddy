from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from core import models
from core.admin import (
    ChildFoodProfileAdmin,
    FoodAdmin,
    MealAdmin,
    MealFoodInline,
)


@override_settings(LANGUAGE_CODE="es")
class FoodAdministrationTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.first()
        cls.user.is_staff = True
        cls.user.is_superuser = True
        cls.user.save(update_fields=["is_staff", "is_superuser"])
        cls.child = models.Child.objects.create(
            first_name="Ana",
            last_name="Prueba",
            birth_date=timezone.localdate(),
        )
        cls.food = models.Food.objects.get(name="Plátano")
        cls.meal = models.Meal.objects.create(
            child=cls.child,
            time=timezone.localtime() - timezone.timedelta(hours=1),
            meal_type="breakfast",
            quantity="normal",
        )
        cls.meal.foods.add(cls.food)
        cls.profile = models.ChildFoodProfile.objects.create(
            child=cls.child,
            food=cls.food,
            taste="likes",
            tolerance="well tolerated",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_models_are_registered_with_expected_admin_classes(self):
        self.assertIsInstance(admin.site._registry[models.Food], FoodAdmin)
        self.assertIsInstance(admin.site._registry[models.Meal], MealAdmin)
        self.assertIsInstance(
            admin.site._registry[models.ChildFoodProfile],
            ChildFoodProfileAdmin,
        )
        self.assertNotIn(models.MealFood, admin.site._registry)
        self.assertEqual(MealAdmin.inlines, (MealFoodInline,))

    def test_food_changelist_can_search_and_filter(self):
        models.Food.objects.create(
            name="Postre de prueba",
            category="dairy",
            active=False,
        )

        response = self.client.get(
            reverse("admin:core_food_changelist"),
            {"q": "Plátano", "active__exact": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plátano")
        self.assertNotContains(response, "Postre de prueba")

    def test_meal_change_page_contains_food_inline(self):
        response = self.client.get(
            reverse("admin:core_meal_change", args=[self.meal.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plátano")

    def test_profile_changelist_can_search(self):
        response = self.client.get(
            reverse("admin:core_childfoodprofile_changelist"),
            {"q": "Plátano"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ana Prueba")
        self.assertContains(response, "Plátano")

    def test_new_admin_texts_are_translated_to_spanish(self):
        with override("es"):
            self.assertEqual(str(models.Food._meta.verbose_name), "Alimento")
            self.assertEqual(str(models.Meal._meta.verbose_name), "Comida")
            self.assertEqual(
                str(models.ChildFoodProfile._meta.verbose_name),
                "Perfil de alimento por niño",
            )
            self.assertEqual(self.profile.get_taste_display(), "Le gusta")
            self.assertEqual(
                self.profile.get_tolerance_display(),
                "Le sienta bien",
            )
