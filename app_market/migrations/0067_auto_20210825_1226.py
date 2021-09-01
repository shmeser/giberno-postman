# Generated by Django 3.1.4 on 2021-08-25 09:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0066_auto_20210823_1541'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributor',
            name='categories',
            field=models.ManyToManyField(related_name='distributors', through='app_market.DistributorCategory', to='app_market.Category'),
        ),
    ]
