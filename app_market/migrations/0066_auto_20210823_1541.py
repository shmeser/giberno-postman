# Generated by Django 3.1.4 on 2021-08-23 12:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_market', '0065_auto_20210803_1247'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profession',
            name='is_suggested',
        ),
        migrations.RemoveField(
            model_name='skill',
            name='is_suggested',
        ),
        migrations.AddField(
            model_name='profession',
            name='suggested_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Предложена пользователем'),
        ),
        migrations.AddField(
            model_name='skill',
            name='suggested_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Предложена пользователем'),
        ),
    ]
