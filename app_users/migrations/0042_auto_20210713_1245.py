# Generated by Django 3.1.4 on 2021-07-13 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0041_userprofile_rating_value'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usermoney',
            name='amount',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
