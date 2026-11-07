from django.db import migrations


def delete_inactive_timers(apps, schema_editor):
    # Importing Timer from core.models would include fields added by later
    # migrations. Their columns don't exist yet when this runs, so the query
    # would fail. This gets Timer as it was when this migration was written.
    Timer = apps.get_model("core", "Timer")
    Timer.objects.filter(active=False).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0026_alter_feeding_end_alter_feeding_start_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="timer",
            options={
                "default_permissions": ("view", "add", "change", "delete"),
                "ordering": ["-start"],
                "verbose_name": "Timer",
                "verbose_name_plural": "Timers",
            },
        ),
        migrations.RemoveField(
            model_name="timer",
            name="duration",
        ),
        migrations.RemoveField(
            model_name="timer",
            name="end",
        ),
        migrations.RunPython(
            delete_inactive_timers, reverse_code=migrations.RunPython.noop
        ),
    ]
