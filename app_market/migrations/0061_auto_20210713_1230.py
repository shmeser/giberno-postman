# Generated by Django 3.1.4 on 2021-07-13 09:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_market', '0060_auto_20210713_1222'),
    ]

    operations = [
        migrations.RenameField(
            model_name='coupon',
            old_name='discount_description',
            new_name='service_description',
        ),
    ]