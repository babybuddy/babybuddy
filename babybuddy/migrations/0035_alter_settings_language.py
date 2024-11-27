from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("babybuddy", "0034_alter_settings_language"),
    ]

    operations = [
        migrations.AlterField(
            model_name="settings",
            name="language",
            field=models.CharField(
                choices=[
                    ("pt-BR", "Brazilian Portuguese"),
                    ("ca", "Catalan"),
                    ("hr", "Croatian"),
                    ("cs", "Czech"),
                    ("zh-hans", "Chinese (simplified)"),
                    ("da", "Danish"),
                    ("nl", "Dutch"),
                    ("en-US", "English (US)"),
                    ("en-GB", "English (UK)"),
                    ("fr", "French"),
                    ("fi", "Finnish"),
                    ("de", "German"),
                    ("he", "Hebrew"),
                    ("hu", "Hungarian"),
                    ("it", "Italian"),
                    ("ja", "Japanese"),
                    ("nb", "Norwegian Bokmål"),
                    ("pl", "Polish"),
                    ("pt", "Portuguese"),
                    ("ru", "Russian"),
                    ("sr", "Serbian"),
                    ("es", "Spanish"),
                    ("sv", "Swedish"),
                    ("tr", "Turkish"),
                    ("uk", "Ukrainian"),
                ],
                default="en-US",
                max_length=255,
                verbose_name="Language",
            ),
        ),
    ]
