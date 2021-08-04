# Generated by Django 3.1.4 on 2021-08-03 09:47

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0064_shiftappealinsurance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftappealinsurance',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Территория страхования'),
        ),
        migrations.AlterField(
            model_name='shiftappealinsurance',
            name='beneficiary',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Выгодоприобретатель'),
        ),
        migrations.AlterField(
            model_name='shiftappealinsurance',
            name='insurance_premium',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Страховая премия'),
        ),
        migrations.AlterField(
            model_name='shiftappealinsurance',
            name='insured_description',
            field=models.TextField(blank=True, max_length=4096, null=True, verbose_name='Застрахованные лица'),
        ),
        migrations.AlterField(
            model_name='shiftappealinsurance',
            name='insurer_sign',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Подпись страховщика'),
        ),
        migrations.AlterField(
            model_name='shiftappealinsurance',
            name='risks',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.JSONField(blank=True, null=True), blank=True, null=True, size=10, verbose_name='Риски'),
        ),
        migrations.AlterField(
            model_name='shiftappealinsurance',
            name='risks_description',
            field=models.TextField(blank=True, max_length=4096, null=True, verbose_name='Доп. описание рисков'),
        ),
        migrations.AlterField(
            model_name='shiftappealinsurance',
            name='special_conditions',
            field=models.TextField(blank=True, max_length=4096, null=True, verbose_name='Особые условия'),
        ),
    ]