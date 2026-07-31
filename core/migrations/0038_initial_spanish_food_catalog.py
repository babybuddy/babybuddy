from django.db import migrations


FOODS = [
    ("Plátano", "fruit", False),
    ("Manzana", "fruit", False),
    ("Pera", "fruit", False),
    ("Naranja", "fruit", False),
    ("Mandarina", "fruit", False),
    ("Fresa", "fruit", False),
    ("Melocotón", "fruit", False),
    ("Albaricoque", "fruit", False),
    ("Ciruela", "fruit", False),
    ("Uva", "fruit", False),
    ("Sandía", "fruit", False),
    ("Melón", "fruit", False),
    ("Kiwi", "fruit", False),
    ("Mango", "fruit", False),
    ("Piña", "fruit", False),
    ("Aguacate", "fruit", False),
    ("Patata", "vegetable", False),
    ("Batata", "vegetable", False),
    ("Zanahoria", "vegetable", False),
    ("Calabacín", "vegetable", False),
    ("Calabaza", "vegetable", False),
    ("Brócoli", "vegetable", False),
    ("Coliflor", "vegetable", False),
    ("Judía verde", "vegetable", False),
    ("Tomate", "vegetable", False),
    ("Espinaca", "vegetable", False),
    ("Acelga", "vegetable", False),
    ("Puerro", "vegetable", False),
    ("Cebolla", "vegetable", False),
    ("Pepino", "vegetable", False),
    ("Berenjena", "vegetable", False),
    ("Pimiento", "vegetable", False),
    ("Pollo", "meat", False),
    ("Pavo", "meat", False),
    ("Ternera", "meat", False),
    ("Cerdo", "meat", False),
    ("Cordero", "meat", False),
    ("Conejo", "meat", False),
    ("Merluza", "fish", False),
    ("Salmón", "fish", True),
    ("Sardina", "fish", True),
    ("Atún", "fish", True),
    ("Bacalao", "fish", True),
    ("Marisco", "fish", True),
    ("Huevo", "egg", True),
    ("Yogur", "dairy", True),
    ("Leche", "dairy", True),
    ("Queso", "dairy", True),
    ("Avena", "cereal", False),
    ("Arroz", "cereal", False),
    ("Trigo", "cereal", True),
    ("Pan", "cereal", True),
    ("Pasta", "cereal", True),
    ("Maíz", "cereal", False),
    ("Quinoa", "cereal", False),
    ("Lenteja", "legume", False),
    ("Garbanzo", "legume", False),
    ("Alubia", "legume", False),
    ("Guisante", "legume", False),
    ("Cacahuete", "nuts", True),
    ("Almendra", "nuts", True),
    ("Nuez", "nuts", True),
    ("Avellana", "nuts", True),
    ("Anacardo", "nuts", True),
    ("Tofu", "other", True),
    ("Aceite de oliva", "other", False),
]


def add_initial_foods(apps, schema_editor):
    Food = apps.get_model("core", "Food")
    database = schema_editor.connection.alias
    existing_names = {
        name.casefold()
        for name in Food.objects.using(database).values_list("name", flat=True)
    }
    foods = []
    for name, category, allergen in FOODS:
        if name.casefold() not in existing_names:
            foods.append(
                Food(
                    name=name,
                    category=category,
                    allergen=allergen,
                    active=True,
                )
            )
            existing_names.add(name.casefold())
    Food.objects.using(database).bulk_create(foods)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0037_food_meal_childfoodprofile"),
    ]

    operations = [
        migrations.RunPython(
            add_initial_foods,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
