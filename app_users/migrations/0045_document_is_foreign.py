# Generated by Django 3.1.4 on 2021-08-06 12:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0044_auto_20210802_1415'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='is_foreign',
            field=models.BooleanField(default=False, verbose_name='Иностранный документ'),
        ),
    ]