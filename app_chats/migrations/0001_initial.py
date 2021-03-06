# Generated by Django 3.1.4 on 2021-03-24 07:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Chat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('target_id', models.PositiveIntegerField(blank=True, null=True)),
                ('target_ct_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Имя модели - объекта обсуждения в чате')),
                ('subject_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Основной участник чата')),
                ('target_ct', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='chat_target_ct', to='contenttypes.contenttype', verbose_name='Объект обсуждения в чате')),
            ],
            options={
                'verbose_name': 'Чат',
                'verbose_name_plural': 'Чаты',
                'db_table': 'app_chats',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=255, null=True)),
                ('text', models.TextField(blank=True, null=True)),
                ('message_type', models.PositiveIntegerField(choices=[(0, 'COMMAND'), (1, 'SIMPLE'), (2, 'INFO'), (3, 'NOTIFICATION'), (4, 'FORM')], default=1)),
                ('form_status', models.PositiveIntegerField(choices=[(0, 'INITIAL'), (1, 'WORKER_CONFIRMED'), (2, 'EMPLOYER_CONFIRMED')], default=0, verbose_name='Статус обработки сообщения с типом "FORM"')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата прочтения собеседником')),
                ('chat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app_chats.chat')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Сообщение в чате',
                'verbose_name_plural': 'Сообщения в чатах',
                'db_table': 'app_chats__messages',
            },
        ),
        migrations.CreateModel(
            name='ChatUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('blocked_at', models.DateTimeField(blank=True, null=True, verbose_name='Дата блокировки')),
                ('chat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_chats.chat')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Участник чата',
                'verbose_name_plural': 'Участники чатов',
                'db_table': 'app_chats__chat_user',
            },
        ),
        migrations.AddField(
            model_name='chat',
            name='users',
            field=models.ManyToManyField(blank=True, related_name='chats', through='app_chats.ChatUser', to=settings.AUTH_USER_MODEL, verbose_name='Участники чата'),
        ),
    ]
