from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0037_alter_diaperchange_color"),
    ]

    operations = [
        migrations.AddField(
            model_name="tummytime",
            name="notes",
            field=models.TextField(blank=True, null=True, verbose_name="Notes"),
        ),
    ]
