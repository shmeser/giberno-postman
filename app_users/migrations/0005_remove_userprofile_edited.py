# Generated by Django 3.1.4 on 2020-12-18 10:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0004_userprofile_edited'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='edited',
        ),
    ]
