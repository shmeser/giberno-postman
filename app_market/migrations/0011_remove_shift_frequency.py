# Generated by Django 3.1.4 on 2021-01-29 08:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0010_auto_20210129_1118'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shift',
            name='frequency',
        ),
    ]
