# Generated by Django 3.1.4 on 2020-12-11 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0004_auto_20201210_1722'),
    ]

    operations = [
        migrations.AddField(
            model_name='socialmodel',
            name='firebase_id',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
