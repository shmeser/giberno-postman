# Generated by Django 3.1.4 on 2021-04-06 09:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_chats', '0005_messagestat'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='read_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Дата прочтения собеседником моего сообщения'),
        ),
    ]