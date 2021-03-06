# Generated by Django 3.1.4 on 2021-06-30 07:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0044_shiftappeal_notify_leaving'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shop',
            name='discount',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='discount_description',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='discount_multiplier',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='discount_terms',
        ),
        migrations.RemoveField(
            model_name='shop',
            name='is_partner',
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('discount', models.PositiveIntegerField(blank=True, null=True, verbose_name='Базовый размер скидки')),
                ('discount_multiplier', models.PositiveIntegerField(blank=True, null=True, verbose_name='Множитель размера скидки')),
                ('discount_terms', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Условия получения')),
                ('discount_description', models.CharField(blank=True, max_length=1024, null=True, verbose_name='Описание услуги')),
                ('distributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_market.distributor')),
            ],
            options={
                'verbose_name': 'Партнер',
                'verbose_name_plural': 'Партнеры',
                'db_table': 'app_market__partners',
            },
        ),
    ]
