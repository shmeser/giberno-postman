# Generated by Django 3.1.4 on 2021-03-18 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0025_auto_20210315_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='rates_count',
            field=models.PositiveIntegerField(default=0, verbose_name='Количество оценок пользователя'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='rating',
            field=models.FloatField(default=0, verbose_name='Рейтинг пользователя'),
        ),
    ]
