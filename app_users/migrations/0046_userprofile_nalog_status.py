# Generated by Django 3.1.4 on 2021-08-31 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0045_document_is_foreign'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='nalog_status',
            field=models.IntegerField(choices=[(0, 'Пользователь не является самозанятым'), (1, 'Пользователь является самозанятым, но не привязан к партнеру'), (2, 'Пользователь самозанятый и привязан к партнеру'), (3, 'Неизвестный статус, возможна ошибка в данных')], default=3, verbose_name='Статус самозанятого'),
        ),
    ]
