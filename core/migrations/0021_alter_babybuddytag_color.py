# Generated by Django 4.0.2 on 2022-02-11 17:27

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_babybuddytag_babybuddytagged_alter_note_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='babybuddytag',
            name='color',
            field=models.CharField(default='#7F7F7F', max_length=32, validators=[core.models.validate_html_color], verbose_name='Color'),
        ),
    ]
