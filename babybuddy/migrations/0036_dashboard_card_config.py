from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("babybuddy", "0035_alter_settings_language"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="dashboard_card_config",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text="Per-card visibility and ordering. Keys are card names, values are dicts with 'visible' (bool) and 'order' (int).",
                verbose_name="Dashboard card configuration",
            ),
        ),
    ]
