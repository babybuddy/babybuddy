from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0036_medication"),
    ]

    operations = [
        migrations.AlterField(
            model_name="diaperchange",
            name="color",
            field=models.CharField(
                blank=True,
                choices=[
                    ("black", "Black"),
                    ("brown", "Brown"),
                    ("gray", "Gray"),
                    ("green", "Green"),
                    ("orange", "Orange"),
                    ("red", "Red"),
                    ("white", "White"),
                    ("yellow", "Yellow"),
                ],
                max_length=255,
                verbose_name="Color",
            ),
        ),
    ]
