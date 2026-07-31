from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core import models, timeline


@override_settings(LANGUAGE_CODE="es")
class MealTimelineTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="meal-timeline-user",
            password="password",
        )
        cls.user.settings.language = "es"
        cls.user.settings.save(update_fields=["language"])
        cls.child = models.Child.objects.create(
            first_name="Ana",
            birth_date=timezone.localdate(),
        )
        cls.food = models.Food.objects.get(name="Plátano")
        cls.meal = models.Meal.objects.create(
            child=cls.child,
            time=timezone.localtime().replace(microsecond=0)
            - timezone.timedelta(hours=1),
            meal_type="breakfast",
            quantity="normal",
            preparation="pieces",
            notes="Comió bien",
        )
        cls.meal.foods.add(cls.food)
        cls.meal.tags.add("favorita")

    def setUp(self):
        self.client.force_login(self.user)

    def grant(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label="core",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    def test_meal_event_contains_details_tags_and_edit_link(self):
        day = timezone.localtime(self.meal.time).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        events = timeline.get_objects(day, self.child)
        event = next(item for item in events if item["model_name"] == "meal")

        self.assertIn("Plátano", event["details"])
        self.assertIn("Cantidad aproximada: Normal", event["details"])
        self.assertIn("Preparación: Trozos", event["details"])
        self.assertIn("Comió bien", event["details"])
        self.assertEqual(list(event["tags"]), list(self.meal.tags.all()))
        self.assertEqual(
            event["edit_link"],
            reverse("core:meal-update", args=[self.meal.pk]),
        )
        self.assertEqual(event["icon"], "feeding")

    def test_child_timeline_respects_meal_view_and_change_permissions(self):
        self.grant("view_child")
        url = reverse("core:child", args=[self.child.slug])

        response = self.client.get(url)
        self.assertNotContains(response, "Plátano")

        self.grant("view_meal")
        response = self.client.get(url)
        self.assertContains(response, "Plátano")
        self.assertNotContains(
            response,
            reverse("core:meal-update", args=[self.meal.pk]),
        )

        self.grant("change_meal")
        response = self.client.get(url)
        self.assertContains(
            response,
            reverse("core:meal-update", args=[self.meal.pk]),
        )


@override_settings(LANGUAGE_CODE="es")
class MealDailySummaryTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="meal-summary-user",
            password="password",
        )
        cls.user.settings.language = "es"
        cls.user.settings.pagination_count = 1
        cls.user.settings.save(update_fields=["language", "pagination_count"])
        cls.child = models.Child.objects.create(
            first_name="Ana",
            birth_date=timezone.localdate(),
        )
        cls.banana = models.Food.objects.get(name="Plátano")
        cls.oats = models.Food.objects.get(name="Avena")
        cls.yogurt = models.Food.objects.get(name="Yogur")
        now = timezone.localtime().replace(microsecond=0)
        breakfast = models.Meal.objects.create(
            child=cls.child,
            time=now - timezone.timedelta(hours=2),
            meal_type="breakfast",
        )
        breakfast.foods.add(cls.banana, cls.oats)
        snack = models.Meal.objects.create(
            child=cls.child,
            time=now - timezone.timedelta(hours=1),
            meal_type="snack",
        )
        snack.foods.add(cls.banana, cls.yogurt)

    def setUp(self):
        self.client.force_login(self.user)
        permission = Permission.objects.get(
            content_type__app_label="core",
            codename="view_meal",
        )
        self.user.user_permissions.add(permission)

    def test_daily_summary_uses_complete_filtered_day_across_pagination(self):
        response = self.client.get(reverse("core:meal-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["object_list"]), 1)
        summary = response.context["object_list"][0].day_summary
        self.assertEqual(summary["meal_count"], 2)
        self.assertEqual(summary["food_count"], 3)
        self.assertCountEqual(
            summary["category_counts"],
            [("Cereal", 1), ("Fruta", 2), ("Lácteo", 1)],
        )
        self.assertCountEqual(
            summary["new_foods"],
            ["Avena", "Plátano", "Yogur"],
        )
        self.assertContains(response, "Resumen diario")
        self.assertContains(response, "Comidas: 2")
        self.assertContains(response, "Alimentos diferentes: 3")
        self.assertContains(response, "Primeras introducciones")

    def test_daily_summary_respects_meal_filters(self):
        response = self.client.get(
            reverse("core:meal-list"),
            {"food": self.yogurt.pk, "filtered": "1"},
        )

        summary = response.context["object_list"][0].day_summary
        self.assertEqual(summary["meal_count"], 1)
        self.assertEqual(summary["food_count"], 2)
        self.assertCountEqual(summary["new_foods"], ["Yogur"])
