from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0038_initial_spanish_food_catalog"),
    ]

    operations = [
        migrations.AddField(
            model_name="sleep",
            name="wakeups",
            field=models.PositiveIntegerField(default=0, verbose_name="Wake-ups"),
        ),
    ]
