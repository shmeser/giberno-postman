# Generated by Django 3.1.4 on 2021-06-28 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0043_auto_20210622_1509'),
    ]

    operations = [
        migrations.AddField(
            model_name='shiftappeal',
            name='notify_leaving',
            field=models.BooleanField(default=True),
        ),
    ]
