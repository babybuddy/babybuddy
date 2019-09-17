# Generated by Django 2.2.1 on 2019-06-07 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20190607_1422'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feeding',
            name='type',
            field=models.CharField(choices=[('breast milk', 'Breast milk'), ('formula', 'Formula'), ('fortified breast milk', 'Fortified breast milk'), ('vegetable food', 'Vegetable Food'), ('fruit', 'fruit'), ('bread', 'Bread')], max_length=255, verbose_name='Type'),
        ),
    ]
