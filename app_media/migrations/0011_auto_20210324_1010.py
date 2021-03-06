# Generated by Django 3.1.4 on 2021-03-24 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_media', '0010_merge_20210315_2253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediamodel',
            name='type',
            field=models.IntegerField(blank=True, choices=[(0, 'OTHER'), (1, 'AVATAR'), (2, 'PASSPORT'), (3, 'INN'), (4, 'SNILS'), (5, 'MEDICAL_BOOK'), (6, 'DRIVER_LICENCE'), (7, 'LOGO'), (8, 'FLAG'), (9, 'BANNER'), (10, 'MAP'), (11, 'NOTIFICATION_ICON'), (12, 'ATTACHMENT')], null=True, verbose_name='Принадлежность'),
        ),
    ]
