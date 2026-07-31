from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core import forms, models


@override_settings(LANGUAGE_CODE="es")
class ChildFoodProfileViewsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="profile-user",
            password="password",
        )
        cls.user.settings.language = "es"
        cls.user.settings.save(update_fields=["language"])
        cls.child = models.Child.objects.create(
            first_name="Ana",
            birth_date=timezone.localdate(),
        )
        cls.other_child = models.Child.objects.create(
            first_name="Leo",
            birth_date=timezone.localdate(),
        )
        cls.banana = models.Food.objects.get(name="Plátano")
        cls.oats = models.Food.objects.get(name="Avena")
        cls.profile = models.ChildFoodProfile.objects.create(
            child=cls.child,
            food=cls.banana,
            taste="likes",
            tolerance="well tolerated",
            notes="Le encanta",
        )

    def setUp(self):
        self.client.force_login(self.user)

    def grant(self, *codenames):
        permissions = Permission.objects.filter(
            content_type__app_label="core",
            codename__in=codenames,
        )
        self.user.user_permissions.add(*permissions)

    def test_profile_form_only_offers_active_foods_but_keeps_existing_food(self):
        self.banana.active = False
        self.banana.save(update_fields=["active"])

        new_form = forms.ChildFoodProfileForm()
        edit_form = forms.ChildFoodProfileForm(instance=self.profile)

        self.assertNotIn(self.banana, new_form.fields["food"].queryset)
        self.assertIn(self.banana, edit_form.fields["food"].queryset)
        self.assertTrue(edit_form.fields["child"].disabled)
        self.assertTrue(edit_form.fields["food"].disabled)

    def test_view_permission_allows_list_but_not_changes(self):
        self.grant("view_childfoodprofile")

        response = self.client.get(reverse("core:child-food-profile-list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plátano")
        self.assertEqual(
            self.client.get(reverse("core:child-food-profile-add")).status_code,
            403,
        )

    def test_profile_navigation_is_in_measurements_menu(self):
        self.grant("view_childfoodprofile", "add_childfoodprofile")

        response = self.client.get(reverse("core:child-food-profile-list"))
        content = response.content.decode()
        measurements = content.split(
            'aria-labelledby="nav-measurements-menu-link"', 1
        )[1].split('</div>\n</li>', 1)[0]
        activities = content.split(
            'aria-labelledby="nav-activity-menu-link"', 1
        )[1].split('</div>\n</li>', 1)[0]

        self.assertIn(reverse("core:child-food-profile-list"), measurements)
        self.assertIn(reverse("core:child-food-profile-add"), measurements)
        self.assertNotIn(reverse("core:child-food-profile-list"), activities)
        self.assertEqual(
            self.client.get(
                reverse("core:child-food-profile-update", args=[self.profile.pk])
            ).status_code,
            403,
        )

    def test_authorized_user_can_add_and_edit_profile(self):
        self.grant(
            "view_childfoodprofile",
            "add_childfoodprofile",
            "change_childfoodprofile",
        )

        response = self.client.post(
            reverse("core:child-food-profile-add"),
            {
                "child": self.other_child.pk,
                "food": self.oats.pk,
                "taste": "indifferent",
                "tolerance": "well tolerated",
                "notes": "Primera valoración",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        profile = models.ChildFoodProfile.objects.get(
            child=self.other_child,
            food=self.oats,
        )
        self.assertEqual(profile.taste, "indifferent")

        response = self.client.post(
            reverse("core:child-food-profile-update", args=[profile.pk]),
            {
                "child": self.other_child.pk,
                "food": self.oats.pk,
                "taste": "likes very much",
                "tolerance": "poorly tolerated",
                "notes": "Revisado",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        profile.refresh_from_db()
        self.assertEqual(profile.taste, "likes very much")
        self.assertEqual(profile.tolerance, "poorly tolerated")

    def test_profile_list_filters_and_displays_consumption_statistics(self):
        first_time = timezone.localtime() - timezone.timedelta(days=3)
        last_time = timezone.localtime() - timezone.timedelta(hours=2)
        for meal_time in (first_time, last_time):
            meal = models.Meal.objects.create(
                child=self.child,
                time=meal_time,
                meal_type="lunch",
            )
            meal.foods.add(self.banana)
        other_meal = models.Meal.objects.create(
            child=self.other_child,
            time=timezone.localtime() - timezone.timedelta(days=10),
            meal_type="lunch",
        )
        other_meal.foods.add(self.banana)
        self.grant("view_childfoodprofile")

        response = self.client.get(
            reverse("core:child-food-profile-list"),
            {"child": self.child.pk, "taste": "likes", "filtered": "1"},
        )

        self.assertEqual(response.status_code, 200)
        listed_profile = response.context["object_list"][0]
        self.assertEqual(listed_profile.consumption_count, 2)
        self.assertEqual(listed_profile.first_consumed, first_time)
        self.assertEqual(listed_profile.last_consumed, last_time)
        self.assertContains(response, "Primera ingesta")
        self.assertContains(response, "Veces consumido")


class FoodIntroductionCalculationsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="introduction-user",
            password="password",
        )
        cls.user.settings.language = "es"
        cls.user.settings.save(update_fields=["language"])
        cls.child = models.Child.objects.create(
            first_name="Ana",
            birth_date=timezone.localdate(),
        )
        cls.other_child = models.Child.objects.create(
            first_name="Leo",
            birth_date=timezone.localdate(),
        )
        cls.food = models.Food.objects.get(name="Plátano")

    def setUp(self):
        self.client.force_login(self.user)
        permission = Permission.objects.get(
            content_type__app_label="core",
            codename="view_meal",
        )
        self.user.user_permissions.add(permission)

    def create_meal(self, child, when):
        meal = models.Meal.objects.create(
            child=child,
            time=when,
            meal_type="lunch",
        )
        meal.foods.add(self.food)
        return meal

    def test_first_introduction_is_independent_for_each_child(self):
        first = self.create_meal(
            self.child,
            timezone.localtime() - timezone.timedelta(days=2),
        )
        second = self.create_meal(
            self.child,
            timezone.localtime() - timezone.timedelta(days=1),
        )
        other_child_first = self.create_meal(
            self.other_child,
            timezone.localtime() - timezone.timedelta(hours=1),
        )

        self.assertTrue(first.mealfood_set.get().is_first_introduction)
        self.assertFalse(second.mealfood_set.get().is_first_introduction)
        self.assertTrue(
            other_child_first.mealfood_set.get().is_first_introduction
        )

        response = self.client.get(reverse("core:meal-list"))
        meals = {meal.pk: meal for meal in response.context["object_list"]}

        self.assertTrue(meals[first.pk].mealfood_set.all()[0].is_first_introduction)
        self.assertFalse(meals[second.pk].mealfood_set.all()[0].is_first_introduction)
        self.assertTrue(
            meals[other_child_first.pk].mealfood_set.all()[0].is_first_introduction
        )
        self.assertContains(response, "Nuevo", count=2)
