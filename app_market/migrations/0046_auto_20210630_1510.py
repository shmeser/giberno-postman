# Generated by Django 3.1.4 on 2021-06-30 12:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app_market', '0045_auto_20210630_1033'),
    ]

    operations = [
        migrations.CreateModel(
            name='Achievement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('name', models.CharField(blank=True, max_length=512, null=True)),
                ('description', models.CharField(blank=True, max_length=3072, null=True)),
                ('actions_min_count', models.PositiveIntegerField(default=1, verbose_name='Количество действий для получения достижения')),
                ('type', models.PositiveIntegerField(blank=True, choices=[(1, 'SAME_DISTRIBUTOR_SHIFT'), (2, 'EARLY_SHIFT')], null=True)),
            ],
            options={
                'verbose_name': 'Достижение',
                'verbose_name_plural': 'Достижения',
                'db_table': 'app_market__achievements',
            },
        ),
        migrations.CreateModel(
            name='AchievementProgress',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('actions_min_count', models.PositiveIntegerField(default=1, verbose_name='Количество действий для получения достижения')),
                ('actions_count', models.PositiveIntegerField(default=0, verbose_name='Количество выполненных действий')),
                ('completed_at', models.DateTimeField(verbose_name='Время завершения прогресса по достижению')),
                ('achievement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_market.achievement')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Прогресс пользователя по достижению',
                'verbose_name_plural': 'Прогресс пользователей по достижениям',
                'db_table': 'app_market__achievement_progress',
            },
        ),
        migrations.DeleteModel(
            name='UserShift',
        ),
    ]
