# Generated by Django 3.1.4 on 2021-01-20 07:44

import app_users.enums
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0004_skill_userskill'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('title', models.CharField(blank=True, max_length=128, null=True)),
                ('description', models.CharField(blank=True, max_length=2048, null=True)),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'db_table': 'app_market__categories',
            },
        ),
        migrations.RemoveField(
            model_name='distributor',
            name='category',
        ),
        migrations.AlterField(
            model_name='distributor',
            name='required_docs',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(choices=[('Пасспорт', app_users.enums.DocumentType['PASSPORT']), ('ИНН', app_users.enums.DocumentType['INN']), ('СНИЛС', app_users.enums.DocumentType['SNILS']), ('Медкнижка', app_users.enums.DocumentType['MEDICAL_BOOK']), ('Водительское удостоверение', app_users.enums.DocumentType['DRIVER_LICENCE'])]), size=None),
        ),
        migrations.AlterField(
            model_name='vacancy',
            name='required_docs',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveIntegerField(choices=[('Пасспорт', app_users.enums.DocumentType['PASSPORT']), ('ИНН', app_users.enums.DocumentType['INN']), ('СНИЛС', app_users.enums.DocumentType['SNILS']), ('Медкнижка', app_users.enums.DocumentType['MEDICAL_BOOK']), ('Водительское удостоверение', app_users.enums.DocumentType['DRIVER_LICENCE'])]), size=None, verbose_name='Документы'),
        ),
        migrations.CreateModel(
            name='DistributorCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_market.category')),
                ('distributor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app_market.distributor')),
            ],
            options={
                'verbose_name': 'Категория торговой сети',
                'verbose_name_plural': 'Категории торговых сетей',
                'db_table': 'app_market__distributor_category',
            },
        ),
        migrations.AddField(
            model_name='distributor',
            name='categories',
            field=models.ManyToManyField(related_name='categories', through='app_market.DistributorCategory', to='app_market.Category'),
        ),
    ]
