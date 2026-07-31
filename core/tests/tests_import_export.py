# -*- coding: utf-8 -*-
import datetime
import importlib
import os
import tablib

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core import admin, models


class ImportTestCase(TestCase):
    base_path = os.path.dirname(__file__) + "/import/"
    admin_module = importlib.import_module("core.admin")
    model_module = importlib.import_module("core.models")

    def setUp(self):
        call_command("migrate", verbosity=0)
        # The data to be imported uses 2020-02-10 as a basis and Child ID 1.
        birth_date = datetime.date(year=2020, month=2, day=10)
        models.Child.objects.create(
            first_name="Child", last_name="One", birth_date=birth_date
        ).save()

    def get_dataset(self, model_name):
        with open(self.base_path + model_name + ".csv", "r") as f:
            data = f.read()
        return tablib.Dataset().load(data)

    def import_data(self, model, count):
        dataset = self.get_dataset(model._meta.model_name)
        resource_class = getattr(
            self.admin_module, model.__name__ + "ImportExportResource"
        )
        resource = resource_class()
        result = resource.import_data(dataset, dry_run=False)
        self.assertFalse(result.has_validation_errors())
        self.assertFalse(result.has_errors())
        self.assertEqual(model.objects.count(), count)

    def test_bmi(self):
        self.import_data(models.BMI, 5)

    def test_child(self):
        self.import_data(models.Child, 2)

    def test_child_invalid(self):
        dataset = self.get_dataset("diaperchange-invalid-child")
        resource = admin.DiaperChangeImportExportResource()
        result = resource.import_data(dataset, dry_run=False)
        self.assertTrue(result.has_validation_errors())

    def test_diaperchange(self):
        self.import_data(models.DiaperChange, 75)

    def test_feeding(self):
        self.import_data(models.Feeding, 40)

    def test_headercircumference(self):
        self.import_data(models.HeadCircumference, 5)

    def test_height(self):
        self.import_data(models.Height, 5)

    def test_note(self):
        self.import_data(models.Note, 1)

    def test_pumping(self):
        self.import_data(models.Pumping, 23)

    def test_sleep(self):
        self.import_data(models.Sleep, 39)

    def test_tag(self):
        self.import_data(models.Tag, 10)

    def test_tagged(self):
        self.import_data(models.Tag, 10)
        self.import_data(models.Temperature, 23)
        tests = [
            (65, ["ten", "method"]),
            (70, ["our", "you", "everybody", "ten", "military"]),
            (71, ["you", "treatment", "method"]),
            (75, ["everybody"]),
            (78, ["our", "treatment", "surface"]),
        ]
        for pk, tags in tests:
            entry = models.Temperature.objects.get(pk=pk)
            self.assertQuerySetEqual(entry.tags.names(), tags, ordered=False)

    def test_temperature(self):
        self.import_data(models.Temperature, 23)

    def test_tummytime(self):
        self.import_data(models.TummyTime, 36)

    def test_weight(self):
        self.import_data(models.Weight, 5)


class FoodImportExportTestCase(TestCase):
    def setUp(self):
        self.child = models.Child.objects.create(
            first_name="Lucía",
            last_name="Pruebas",
            birth_date=datetime.date(2025, 1, 1),
        )
        self.food = models.Food.objects.create(
            name="Alimento exportable",
            category="vegetable",
            notes="Datos ficticios",
        )

    def assert_import_succeeded(self, result):
        self.assertFalse(result.has_validation_errors(), result.invalid_rows)
        self.assertFalse(result.has_errors(), result.row_errors())

    def test_food_export_can_be_reimported(self):
        resource = admin.FoodImportExportResource()
        dataset = resource.export(models.Food.objects.filter(pk=self.food.pk))
        self.assertEqual(
            dataset.headers,
            ["id", "name", "category", "allergen", "notes", "active"],
        )
        self.assertEqual(dataset.dict[0]["category"], "vegetable")

        food_id = self.food.pk
        self.food.delete()
        result = resource.import_data(dataset, dry_run=False)
        self.assert_import_succeeded(result)
        self.assertTrue(
            models.Food.objects.filter(pk=food_id, name="Alimento exportable").exists()
        )

    def test_meal_export_preserves_foods_and_tags_when_reimported(self):
        second_food = models.Food.objects.create(name="Segundo alimento", category="fruit")
        meal = models.Meal.objects.create(
            child=self.child,
            time=timezone.now() - datetime.timedelta(hours=1),
            meal_type="lunch",
            quantity="normal",
            preparation="pieces",
            notes="Comida ficticia",
        )
        meal.foods.add(self.food, second_food)
        meal.tags.add("favorita", "prueba")
        resource = admin.MealImportExportResource()
        dataset = resource.export(models.Meal.objects.filter(pk=meal.pk))

        row = dataset.dict[0]
        self.assertEqual(str(row["child_id"]), str(self.child.pk))
        self.assertEqual(row["meal_type"], "lunch")
        self.assertCountEqual(
            row["food_ids"].split(","),
            [str(self.food.pk), str(second_food.pk)],
        )
        self.assertEqual(row["food_names"], "Alimento exportable; Segundo alimento")

        meal_id = meal.pk
        meal.delete()
        result = resource.import_data(dataset, dry_run=False)
        self.assert_import_succeeded(result)
        imported = models.Meal.objects.get(pk=meal_id)
        self.assertCountEqual(
            imported.foods.values_list("pk", flat=True),
            [self.food.pk, second_food.pk],
        )
        self.assertCountEqual(imported.tags.names(), ["favorita", "prueba"])

    def test_food_profile_export_can_be_reimported(self):
        profile = models.ChildFoodProfile.objects.create(
            child=self.child,
            food=self.food,
            taste="likes",
            tolerance="well tolerated",
            notes="Sin incidencias",
        )
        resource = admin.ChildFoodProfileImportExportResource()
        dataset = resource.export(
            models.ChildFoodProfile.objects.filter(pk=profile.pk)
        )
        row = dataset.dict[0]
        self.assertEqual(row["food_id"], str(self.food.pk))
        self.assertEqual(row["food_name"], self.food.name)

        profile_id = profile.pk
        profile.delete()
        result = resource.import_data(dataset, dry_run=False)
        self.assert_import_succeeded(result)
        imported = models.ChildFoodProfile.objects.get(pk=profile_id)
        self.assertEqual(imported.child, self.child)
        self.assertEqual(imported.food, self.food)
        self.assertEqual(imported.taste, "likes")
