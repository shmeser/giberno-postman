# Generated by Django 3.1.4 on 2021-05-18 06:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_chats', '0017_auto_20210513_0954'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='json',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
