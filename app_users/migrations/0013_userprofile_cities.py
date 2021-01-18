# Generated by Django 3.1.4 on 2021-01-13 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_geo', '0006_auto_20210111_1352'),
        ('app_users', '0012_auto_20210113_1522'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='cities',
            field=models.ManyToManyField(blank=True, related_name='cities', through='app_users.UserCity', to='app_geo.City'),
        ),
    ]