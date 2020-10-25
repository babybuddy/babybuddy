# Generated by Django 3.1.2 on 2020-10-25 03:22

import datetime

from django.db import migrations, models
from django.utils import timezone


def pre_alter_birth_date(apps, schema_editor):
    """
    Before migration, copy current birth date to a temporary field.

    :param apps:
    :param schema_editor:
    :return:
    """
    Child = apps.get_model('core', 'Child')
    for child in Child.objects.all():
        combined = datetime.datetime.combine(child.birth_date,
                                             datetime.time(0, 0, 0))
        child.birth_date_temp = timezone.localtime(timezone.make_aware(
            combined))
        child.save()


def post_alter_birth_date(apps, schema_editor):
    """
    After migration, copy datetime value from temporary field to regular field.

    :param apps:
    :param schema_editor:
    :return:
    """
    Child = apps.get_model('core', 'Child')
    for child in Child.objects.all():
        child.birth_date = child.birth_date_temp
        child.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20200813_0238'),
    ]

    operations = [
        migrations.AddField(
            model_name='child',
            name='birth_date_temp',
            field=models.DateTimeField(null=True)
        ),
        migrations.RunPython(pre_alter_birth_date),
        migrations.AlterField(
            model_name='child',
            name='birth_date',
            field=models.DateTimeField(verbose_name='Birth date'),
        ),
        migrations.RunPython(post_alter_birth_date),
        migrations.RemoveField(model_name='child', name='birth_date_temp'),
    ]
