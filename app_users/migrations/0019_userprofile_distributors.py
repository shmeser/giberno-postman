# Generated by Django 3.1.4 on 2021-02-16 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0014_auto_20210208_1558'),
        ('app_users', '0018_notification_icon_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='distributors',
            field=models.ManyToManyField(blank=True, related_name='distributors', to='app_market.Distributor', verbose_name='Торговая сеть'),
        ),
    ]
