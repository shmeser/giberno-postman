# Generated by Django 3.1.4 on 2021-06-30 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_media', '0012_auto_20210429_1601'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediamodel',
            name='type',
            field=models.IntegerField(blank=True, choices=[(0, 'OTHER'), (1, 'AVATAR'), (2, 'PASSPORT'), (3, 'INN'), (4, 'SNILS'), (5, 'MEDICAL_BOOK'), (6, 'DRIVER_LICENCE'), (7, 'LOGO'), (8, 'FLAG'), (9, 'BANNER'), (10, 'MAP'), (11, 'NOTIFICATION_ICON'), (12, 'ATTACHMENT'), (13, 'RULES_AND_ARTICLES'), (14, 'ACHIEVEMENT_ICON')], null=True, verbose_name='Принадлежность'),
        ),
    ]