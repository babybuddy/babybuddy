from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("babybuddy", "0037_settings_dashboard_show_diaperchange_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="settings",
            name="dashboard_card_order",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Comma-separated list of card names in display order. "
                    "Cards not listed appear after, in their default order."
                ),
                max_length=512,
                verbose_name="Dashboard Card Order",
            ),
        ),
    ]
