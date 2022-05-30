# Generated by Django 4.0.4 on 2022-05-30 03:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("babybuddy", "0022_alter_settings_language"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="max_tag_count",
            field=models.IntegerField(
                default=5,
                help_text="The maximum number of tags to display when adding things that have tags",
                verbose_name="Max Tag Count",
            ),
        ),
    ]
