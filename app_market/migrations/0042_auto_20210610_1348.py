# Generated by Django 3.1.4 on 2021-06-10 10:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0041_auto_20210609_1544'),
    ]

    operations = [
        migrations.AddField(
            model_name='shiftappeal',
            name='complete_reason',
            field=models.PositiveIntegerField(blank=True, choices=[(1, 'WORK_IS_DONE'), (2, 'HEALTH_PROBLEM')], null=True, verbose_name='Причина завершения смены'),
        ),
        migrations.AddField(
            model_name='shiftappeal',
            name='complete_reason_text',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Текст причины завершения'),
        ),
    ]
