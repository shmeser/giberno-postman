# Generated by Django 3.2.5 on 2021-07-28 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appcraft_nalog_sdk', '0008_nalogincomerequestmodel_error_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='nalogincomerequestmodel',
            name='canceled_reason',
            field=models.TextField(blank=True, choices=[('REFUND', 'Возврат средств'), ('REGISTRATION_MISTAKE ', 'Чек сформирован ошибочно')], null=True, verbose_name='Причина аннулирования'),
        ),
        migrations.AddField(
            model_name='nalogincomerequestmodel',
            name='is_canceled',
            field=models.BooleanField(default=False, verbose_name='Отменен/Аннулирован'),
        ),
    ]
