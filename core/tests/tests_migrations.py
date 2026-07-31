import datetime
import importlib

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class FoodAndMealMigrationTestCase(TransactionTestCase):
    migrate_from = ("core", "0036_medication")
    migrate_to = ("core", "0037_food_meal_childfoodprofile")

    def setUp(self):
        super().setUp()
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_from])
        old_apps = self.executor.loader.project_state([self.migrate_from]).apps
        Child = old_apps.get_model("core", "Child")
        self.child_id = Child.objects.create(
            first_name="First",
            last_name="Last",
            birth_date=datetime.date(2025, 1, 1),
            slug="first-last",
        ).pk

        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_to])
        self.apps = self.executor.loader.project_state([self.migrate_to]).apps

    def tearDown(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_migration_creates_food_meal_and_relationship(self):
        ChildFoodProfile = self.apps.get_model("core", "ChildFoodProfile")
        Food = self.apps.get_model("core", "Food")
        Meal = self.apps.get_model("core", "Meal")
        MealFood = self.apps.get_model("core", "MealFood")

        food = Food.objects.create(name="Banana", category="fruit")
        meal = Meal.objects.create(
            child_id=self.child_id,
            time=datetime.datetime(2025, 1, 2, 8, 30, tzinfo=datetime.timezone.utc),
            meal_type="breakfast",
        )
        MealFood.objects.create(meal=meal, food=food)
        profile = ChildFoodProfile.objects.create(
            child_id=self.child_id,
            food=food,
            taste="likes",
            tolerance="well tolerated",
        )

        self.assertTrue(food.active)
        self.assertEqual(list(meal.foods.values_list("name", flat=True)), ["Banana"])
        self.assertEqual(profile.taste, "likes")
        self.assertEqual(profile.tolerance, "well tolerated")
        self.assertEqual(Meal._meta.ordering, ["-time", "-id"])


class InitialSpanishFoodCatalogMigrationTestCase(TransactionTestCase):
    migrate_from = ("core", "0037_food_meal_childfoodprofile")
    migrate_to = ("core", "0038_initial_spanish_food_catalog")

    def setUp(self):
        super().setUp()
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_from])
        old_apps = self.executor.loader.project_state([self.migrate_from]).apps
        Food = old_apps.get_model("core", "Food")
        Food.objects.create(
            name="AVENA",
            category="other",
            active=False,
            notes="Valor personalizado",
        )

        self.executor = MigrationExecutor(connection)
        self.executor.migrate([self.migrate_to])
        self.apps = self.executor.loader.project_state([self.migrate_to]).apps

    def tearDown(self):
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_catalog_is_created_without_overwriting_existing_foods(self):
        Food = self.apps.get_model("core", "Food")
        migration = importlib.import_module(
            "core.migrations.0038_initial_spanish_food_catalog"
        )

        self.assertEqual(Food.objects.count(), len(migration.FOODS))
        self.assertTrue(Food.objects.filter(name="Plátano", category="fruit").exists())
        self.assertTrue(
            Food.objects.filter(
                name="Huevo",
                category="egg",
                allergen=True,
            ).exists()
        )
        oats = Food.objects.get(name="AVENA")
        self.assertEqual(oats.category, "other")
        self.assertFalse(oats.active)
        self.assertEqual(oats.notes, "Valor personalizado")
