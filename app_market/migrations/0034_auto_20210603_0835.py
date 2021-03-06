# Generated by Django 3.1.4 on 2021-06-03 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0033_shiftappeal_qr_text'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shiftappeal',
            old_name='time_completed',
            new_name='completed_real_time',
        ),
        migrations.AddField(
            model_name='shiftappeal',
            name='qr_scan_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время сканирования QR кода охранником'),
        ),
        migrations.AddField(
            model_name='shiftappeal',
            name='started_real_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Фактическое время начала смены'),
        ),
    ]
