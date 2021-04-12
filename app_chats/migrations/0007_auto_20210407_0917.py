# Generated by Django 3.1.4 on 2021-04-07 06:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_chats', '0006_auto_20210406_1248'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagestat',
            name='chat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='messages_stats', to='app_chats.chat'),
        ),
        migrations.AlterField(
            model_name='messagestat',
            name='message',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='stats', to='app_chats.message'),
        ),
        migrations.AlterField(
            model_name='messagestat',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='interacted_messages', to=settings.AUTH_USER_MODEL),
        ),
    ]