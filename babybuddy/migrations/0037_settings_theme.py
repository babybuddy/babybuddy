# Generated by Django 5.1.4 on 2025-01-14 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("babybuddy", "0036_alter_settings_timezone"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="theme",
            field=models.CharField(
                choices=[("dark", "Dark"), ("light", "Light"), ("pink", "Pink")],
                default="dark",
                max_length=100,
                verbose_name="Theme",
            ),
        ),
    ]
