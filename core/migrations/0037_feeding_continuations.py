from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0036_medication"),
    ]

    operations = [
        migrations.AddField(
            model_name="feeding",
            name="previous_feeding",
            field=models.ForeignKey(
                blank=True,
                help_text="Link to a feeding this continues (back-to-back sessions).",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="continuations",
                to="core.feeding",
                verbose_name="Previous feeding",
            ),
        ),
    ]
