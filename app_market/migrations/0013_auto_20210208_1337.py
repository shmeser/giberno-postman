# Generated by Django 3.1.4 on 2021-02-08 10:37

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0012_shift_frequency'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shift',
            name='by_month',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(), blank=True, null=True, size=12, verbose_name='Месяцы'),
        ),
    ]
