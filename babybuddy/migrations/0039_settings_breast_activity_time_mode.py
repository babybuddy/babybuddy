from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("babybuddy", "0038_settings_dashboard_card_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="breast_activity_time_mode",
            field=models.CharField(
                blank=True,
                default="end",
                max_length=5,
                choices=[
                    ("end", "End time (current behavior)"),
                    ("start", "Start time"),
                ],
                help_text=(
                    "Controls whether the Last Breast Activity card compares "
                    "and displays the START or END time of activities. "
                    "Defaults to END."
                ),
                verbose_name="Breast Activity Time Mode",
            ),
        ),
    ]
