# Generated by Django 3.2.5 on 2021-07-28 06:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appcraft_nalog_sdk', '0004_nalogbindpartnerrequestmodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='naloguser',
            name='is_tax_payment',
            field=models.BooleanField(default=False, verbose_name='Платим ли налоги за пользователя'),
        ),
    ]
