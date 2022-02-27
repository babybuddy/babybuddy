# Generated by Django 4.0.2 on 2022-02-15 16:33

import core.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("core", "0018_bmi_headcircumference_height"),
    ]

    operations = [
        migrations.CreateModel(
            name="BabyBuddyTag",
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
                    models.CharField(max_length=100, unique=True, verbose_name="name"),
                ),
                (
                    "slug",
                    models.SlugField(max_length=100, unique=True, verbose_name="slug"),
                ),
                (
                    "color",
                    models.CharField(
                        default=core.models.random_color,
                        max_length=32,
                        validators=[
                            django.core.validators.RegexValidator("^#[0-9A-F]{6}$")
                        ],
                        verbose_name="Color",
                    ),
                ),
                ("last_used", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "verbose_name": "Tag",
                "verbose_name_plural": "Tags",
            },
        ),
        migrations.CreateModel(
            name="BabyBuddyTagged",
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
                    "object_id",
                    models.IntegerField(db_index=True, verbose_name="object ID"),
                ),
                (
                    "content_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_tagged_items",
                        to="contenttypes.contenttype",
                        verbose_name="content type",
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_items",
                        to="core.babybuddytag",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="note",
            name="tags",
            field=taggit.managers.TaggableManager(
                blank=True,
                help_text="A comma-separated list of tags.",
                through="core.BabyBuddyTagged",
                to="core.BabyBuddyTag",
                verbose_name="Tags",
            ),
        ),
    ]