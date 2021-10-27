from django.db import migrations, models


def set_napping(apps, schema_editor):
    Sleeps = apps.get_model('core', 'Sleep')
    for sleep in Sleeps.objects.all():
        sleep.napping = sleep.nap
        sleep.save()


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0014_alter_child_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='sleep',
            name='napping',
            field=models.BooleanField(null=True, verbose_name='Napping'),
        ),
        migrations.RunPython(set_napping, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='sleep',
            name='napping',
            field=models.BooleanField(verbose_name='Napping'),
        ),
    ]
