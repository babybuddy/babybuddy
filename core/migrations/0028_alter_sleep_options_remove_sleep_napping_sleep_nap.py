# Generated by Django 4.2 on 2023-05-06 15:35

from django.db import migrations, models
from django.utils import timezone


def set_sleep_nap_values(apps, schema_editor):
    # The model must be imported to ensure its overridden `save` method is run.
    from core.models import Sleep

    for sleep in Sleep.objects.all():
        sleep.nap = (
            Sleep.settings.nap_start_min
            <= timezone.localtime(sleep.start).time()
            <= Sleep.settings.nap_start_max
        )
        sleep.save()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0027_alter_timer_options_remove_timer_duration_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="sleep",
            options={
                "default_permissions": ("view", "add", "change", "delete"),
                "ordering": ["-start"],
                "permissions": [("can_edit_sleep_settings", "Can edit Sleep settings")],
                "verbose_name": "Sleep",
                "verbose_name_plural": "Sleep",
            },
        ),
        migrations.RemoveField(
            model_name="sleep",
            name="napping",
        ),
        migrations.AddField(
            model_name="sleep",
            name="nap",
            field=models.BooleanField(null=True, verbose_name="Nap"),
        ),
        migrations.RunPython(
            set_sleep_nap_values, reverse_code=migrations.RunPython.noop
        ),
    ]
