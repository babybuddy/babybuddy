from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ("babybuddy", "0016_alter_settings_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="dashboard_hide_age",
            field=models.DurationField(
                choices=[
                    (None, "show all data"),
                    (timezone.timedelta(days=1), "1 day"),
                    (timezone.timedelta(days=2), "2 days"),
                    (timezone.timedelta(days=3), "3 days"),
                    (timezone.timedelta(weeks=1), "1 week"),
                    (timezone.timedelta(weeks=4), "4 weeks"),
                ],
                default=None,
                null=True,
                verbose_name="Hide data older than",
            ),
        ),
    ]
