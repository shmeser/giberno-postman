# Generated by Django 3.1.4 on 2021-08-02 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_media', '0015_auto_20210716_1146'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mediamodel',
            name='type',
            field=models.IntegerField(blank=True, choices=[(0, 'OTHER'), (1, 'AVATAR'), (2, 'PASSPORT'), (3, 'INN'), (4, 'SNILS'), (5, 'MEDICAL_BOOK'), (6, 'DRIVER_LICENCE'), (7, 'LOGO'), (8, 'FLAG'), (9, 'BANNER'), (10, 'MAP'), (11, 'NOTIFICATION_ICON'), (12, 'ATTACHMENT'), (13, 'RULES_AND_ARTICLES'), (14, 'ACHIEVEMENT_ICON'), (15, 'PROMO_TERMS'), (16, 'PARTNERS_SHOP_TERMS'), (17, 'MARKETING_POLICY'), (18, 'PRIZE_IMAGE'), (19, 'VACCINATION_CERTIFICATE'), (20, 'VISA'), (21, 'RESIDENT_CARD'), (22, 'MIGRATION_CARD')], null=True, verbose_name='Принадлежность'),
        ),
    ]
