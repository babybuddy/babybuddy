import core.models
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


def rename_medicine_if_exists(apps, schema_editor):
    tables = schema_editor.connection.introspection.table_names()
    if "core_medicine" in tables:
        schema_editor.execute("ALTER TABLE core_medicine RENAME TO core_medication")
        schema_editor.execute(
            "DELETE FROM django_migrations WHERE app='core' AND name='0036_medicine'"
        )


def create_if_not_exists(apps, schema_editor):
    tables = schema_editor.connection.introspection.table_names()
    if "core_medication" not in tables:
        Medication = apps.get_model("core", "Medication")
        schema_editor.create_model(Medication)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0035_recalculate_durations"),
    ]

    operations = [
        migrations.RunPython(rename_medicine_if_exists, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="Medication",
                    fields=[
                        (
                            "id",
                            models.AutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "name",
                            models.CharField(
                                db_index=True,
                                help_text="Name of the medication administered",
                                max_length=255,
                                verbose_name="Medication Name",
                            ),
                        ),
                        (
                            "dosage",
                            models.FloatField(
                                blank=True,
                                help_text="Amount of medication given",
                                null=True,
                                verbose_name="Dosage",
                            ),
                        ),
                        (
                            "dosage_unit",
                            models.CharField(
                                blank=True,
                                choices=[
                                    ("mg", "MG"),
                                    ("ml", "ML"),
                                    ("tablets", "Tablets"),
                                    ("drops", "Drops"),
                                ],
                                default="",
                                max_length=20,
                                verbose_name="Dosage Unit",
                            ),
                        ),
                        (
                            "time",
                            models.DateTimeField(
                                db_index=True,
                                default=django.utils.timezone.localtime,
                                verbose_name="Time Taken",
                            ),
                        ),
                        (
                            "next_dose_interval",
                            models.DurationField(
                                blank=True,
                                help_text="Time until next dose can be given",
                                null=True,
                                verbose_name="Next Dose Interval",
                            ),
                        ),
                        (
                            "notes",
                            models.TextField(
                                blank=True, null=True, verbose_name="Notes"
                            ),
                        ),
                        (
                            "child",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="medication",
                                to="core.child",
                                verbose_name="Child",
                            ),
                        ),
                        (
                            "tags",
                            core.models.TaggableManager(
                                blank=True,
                                help_text="A comma-separated list of tags.",
                                through="core.Tagged",
                                to="core.Tag",
                                verbose_name="Tags",
                            ),
                        ),
                    ],
                    options={
                        "verbose_name": "Medication",
                        "verbose_name_plural": "Medications",
                        "ordering": ["-time"],
                        "default_permissions": ("view", "add", "change", "delete"),
                    },
                ),
            ],
        ),
        migrations.RunPython(create_if_not_exists, migrations.RunPython.noop),
    ]
