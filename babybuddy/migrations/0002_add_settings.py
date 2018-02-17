# -*- coding: utf-8 -*-
from django.db import migrations


def add_settings(apps, schema_editor):
    Settings = apps.get_model('babybuddy', 'Settings')
    User = apps.get_model('auth', 'User')
    for user in User.objects.all():
        if Settings.objects.filter(user=user).count() == 0:
            settings = Settings.objects.create(user=user)
            settings.save()


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('babybuddy', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_settings, reverse_code=migrations.RunPython.noop),
    ]
