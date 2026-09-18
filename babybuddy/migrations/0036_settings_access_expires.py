from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("babybuddy", "0035_alter_settings_language"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="access_expires",
            field=models.DateTimeField(
                blank=True,
                help_text="Optional. After this time the user can no longer sign in or use the API.",
                null=True,
                verbose_name="Access expires",
            ),
        ),
    ]
