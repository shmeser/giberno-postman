# Generated by Django 3.1.4 on 2021-01-18 09:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0002_profession_userprofession'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profession',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Одобрена (для предложенных)'),
        ),
    ]