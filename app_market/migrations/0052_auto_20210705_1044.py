# Generated by Django 3.1.4 on 2021-07-05 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0051_auto_20210705_1033'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.PositiveIntegerField(choices=[(0, 'CREATED'), (1, 'COMPLETED'), (2, 'CANCELED'), (3, 'FAILED'), (4, 'RETURNING'), (5, 'RETURNED')], default=0),
        ),
        migrations.AddField(
            model_name='order',
            name='type',
            field=models.PositiveIntegerField(choices=[(0, 'TEST'), (1, 'GET_COUPON'), (2, 'WITHDRAW_BONUS_BY_VOUCHER')], default=0),
        ),
    ]
