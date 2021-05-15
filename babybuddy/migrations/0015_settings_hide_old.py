from django.db import migrations, models
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('babybuddy', '0014_settings_hide_empty'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='dashboard_hide_old',
            field=models.DurationField(
                choices=[
                    (None, 'show all data'),
                    (timezone.timedelta(days=1), '1 day'),
                    (timezone.timedelta(days=2), '2 days'),
                    (timezone.timedelta(days=3), '3 days'),
                    (timezone.timedelta(weeks=1), '1 week'),
                    (timezone.timedelta(months=1), '1 month')
                ],
                default=None,
                null=True,
                verbose_name='Hide data older than'),
        ),
    ]
