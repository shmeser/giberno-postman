# Generated by Django 3.1.4 on 2021-03-11 08:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_users', '0022_userprofile_password_changed'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='manager_position',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
