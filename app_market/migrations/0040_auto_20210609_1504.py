# Generated by Django 3.1.4 on 2021-06-09 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0039_auto_20210609_0917'),
    ]

    operations = [
        migrations.AlterField(
            model_name='shiftappeal',
            name='manager_cancel_reason',
            field=models.PositiveIntegerField(blank=True, choices=[(1, 'WRONG_DOCUMENTS'), (2, 'UNABLE_TO_WORK')], null=True, verbose_name='Причина отмены менеджером'),
        ),
    ]
