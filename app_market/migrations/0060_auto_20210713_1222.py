# Generated by Django 3.1.4 on 2021-07-13 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0059_partner_color'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='coupon',
            name='discount_amount',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='discount',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='discount_description',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='discount_multiplier',
        ),
        migrations.RemoveField(
            model_name='partner',
            name='discount_terms',
        ),
        migrations.AddField(
            model_name='coupon',
            name='bonus_price',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='coupon',
            name='description',
            field=models.CharField(blank=True, max_length=128, null=True, verbose_name='Описание'),
        ),
        migrations.AddField(
            model_name='coupon',
            name='discount',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Размер скидки'),
        ),
    ]
