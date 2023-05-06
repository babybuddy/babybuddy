from django.db import migrations, models


def set_napping(apps, schema_editor):
    # The model must be imported to ensure its overridden `save` method is run.
    from core import models

    for sleep in models.Sleep.objects.all():
        sleep.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_alter_child_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="sleep",
            name="napping",
            field=models.BooleanField(null=True, verbose_name="Napping"),
        ),
        # Migration superseded by 0028_alter_sleep_options_remove_sleep_napping_sleep_nap.py
        # migrations.RunPython(set_napping, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="sleep",
            name="napping",
            field=models.BooleanField(verbose_name="Napping"),
        ),
    ]
