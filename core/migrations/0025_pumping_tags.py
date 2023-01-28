# Generated by Django 4.1.3 on 2023-01-28 13:59

import core.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0024_alter_tag_slug"),
    ]

    operations = [
        migrations.AddField(
            model_name="pumping",
            name="tags",
            field=core.models.TaggableManager(
                blank=True,
                help_text="A comma-separated list of tags.",
                through="core.Tagged",
                to="core.Tag",
                verbose_name="Tags",
            ),
        ),
    ]
