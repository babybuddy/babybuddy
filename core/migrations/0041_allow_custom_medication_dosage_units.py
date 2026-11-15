from django.core.validators import RegexValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0040_appdata"),
    ]

    operations = [
        migrations.AlterField(
            model_name="medication",
            name="dosage_unit",
            field=models.CharField(
                blank=True,
                default="",
                max_length=20,
                validators=[
                    RegexValidator(
                        r"\A[^\x00-\x1f\x7f-\x9f\u2028\u2029]*\Z",
                        "Enter the dosage unit on one line.",
                    )
                ],
                verbose_name="Dosage Unit",
            ),
        ),
    ]
