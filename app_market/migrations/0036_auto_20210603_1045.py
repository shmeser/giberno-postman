# Generated by Django 3.1.4 on 2021-06-03 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0035_auto_20210603_0902'),
    ]

    operations = [
        migrations.AddField(
            model_name='shiftappeal',
            name='security_pass_refuse_reason',
            field=models.PositiveIntegerField(blank=True, choices=[(0, 'CUSTOM'), (3, 'NO_PASSPORT'), (9, 'MANAGER_SUPPORT_NEED')], null=True, verbose_name='Причина отказа в пропуске охранником'),
        ),
        migrations.AddField(
            model_name='shiftappeal',
            name='security_pass_refuse_reason_text',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Текст причины отказа в пропуске охранником'),
        ),
    ]
