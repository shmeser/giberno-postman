# Generated by Django 3.1.4 on 2020-12-29 08:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0008_socialmodel_is_for_reg'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='show_phone',
            field=models.BooleanField(default=False, verbose_name='Показывать номер телефона'),
        ),
    ]
