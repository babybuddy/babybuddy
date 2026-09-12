from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0036_medication"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpitUp",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "time",
                    models.DateTimeField(
                        blank=False,
                        default=django.utils.timezone.localtime,
                        null=False,
                        verbose_name="Time",
                    ),
                ),
                (
                    "amount",
                    models.CharField(
                        choices=[
                            ("trace", "Trace (just a spot)"),
                            ("dribble", "Dribble (a little)"),
                            ("moderate", "Moderate (noticeable)"),
                            ("large", "Large (soaks clothes)"),
                            ("projectile", "Projectile / lots"),
                        ],
                        blank=True,
                        default="",
                        max_length=50,
                        verbose_name="Amount",
                    ),
                ),
                (
                    "appearance",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=255,
                        verbose_name="Appearance",
                        help_text="e.g., curdled, watery, clear, milky",
                    ),
                ),
                (
                    "notes",
                    models.TextField(blank=True, null=True, verbose_name="Notes"),
                ),
                (
                    "child",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="spit_ups",
                        to="core.child",
                        verbose_name="Child",
                    ),
                ),
                (
                    "related_feeding",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        blank=True,
                        related_name="spit_ups",
                        to="core.feeding",
                        verbose_name="Related feeding",
                    ),
                ),
            ],
            options={
                "verbose_name": "Spit-Up",
                "verbose_name_plural": "Spit-Up",
                "ordering": ["-time"],
                "default_permissions": ("view", "add", "change", "delete"),
            },
        ),
    ]
