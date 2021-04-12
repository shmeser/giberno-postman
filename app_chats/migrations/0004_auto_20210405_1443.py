# Generated by Django 3.1.4 on 2021-04-05 11:43

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('app_chats', '0003_message_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages', to='app_chats.chat'),
        ),
        migrations.AlterField(
            model_name='message',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4),
        ),
    ]