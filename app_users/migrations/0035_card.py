# Generated by Django 3.1.4 on 2021-07-08 05:37

import app_users.enums
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0034_auto_20210629_1416'),
    ]

    operations = [
        migrations.CreateModel(
            name='Card',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('type', models.IntegerField(choices=[(1, 'DEBIT'), (2, 'CREDIT'), (3, 'PREPAID')], default=app_users.enums.CardType['DEBIT'])),
                ('payment_network', models.IntegerField(choices=[(0, 'UNKNOWN'), (1, 'VISA'), (2, 'MASTERCARD'), (3, 'MIR')], default=app_users.enums.CardPaymentNetwork['UNKNOWN'], verbose_name='Платежная сеть')),
                ('number', models.CharField(blank=True, max_length=128, null=True, verbose_name='Маскированный номер карты')),
                ('valid_through', models.CharField(blank=True, max_length=128, null=True, verbose_name='Действительна до')),
                ('issuer', models.CharField(blank=True, max_length=128, null=True, verbose_name='Эмитент карты')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Банковская Карта',
                'verbose_name_plural': 'Банковские Карты',
                'db_table': 'app_users__cards',
            },
        ),
    ]
