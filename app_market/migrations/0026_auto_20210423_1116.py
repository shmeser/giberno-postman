# Generated by Django 3.1.4 on 2021-04-23 08:16

import app_market.enums
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0025_auto_20210422_1148'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftappeal',
            name='status',
            field=models.PositiveIntegerField(choices=[(0, 'INITIAL'), (1, 'CONFIRMED'), (2, 'CANCELED'), (3, 'REJECTED'), (4, 'COMPLETED')], default=app_market.enums.ShiftAppealStatus['INITIAL']),
        ),
    ]