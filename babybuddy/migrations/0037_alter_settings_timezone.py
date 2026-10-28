import babybuddy.timezones
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("babybuddy", "0036_settings_access_expires"),
    ]

    operations = [
        migrations.AlterField(
            model_name="settings",
            name="timezone",
            field=models.CharField(
                choices=babybuddy.timezones.timezone_choices,
                default="UTC",
                max_length=100,
                verbose_name="Timezone",
            ),
        ),
    ]
