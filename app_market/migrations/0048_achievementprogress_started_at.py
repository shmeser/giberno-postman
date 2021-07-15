# Generated by Django 3.1.4 on 2021-07-02 06:45

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0047_advertisement'),
    ]

    operations = [
        migrations.AddField(
            model_name='achievementprogress',
            name='started_at',
            field=models.DateTimeField(default=datetime.datetime(2021, 7, 2, 6, 45, 55, 263607, tzinfo=utc), verbose_name='Время начала накопления прогресса по достижению'),
            preserve_default=False,
        ),
    ]