# Generated by Django 3.1.4 on 2021-01-14 08:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('app_media', '0004_auto_20210114_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediamodel',
            name='owner_ct',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='mediamodel',
            name='owner_ct_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='mediamodel',
            name='owner_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RunSQL(
            '''
            UPDATE app_media 
            SET 
                "owner_id" = "_owner_id", 
                "owner_ct_id" = "_owner_content_type_id", 
                "owner_ct_name" = "_owner_content_type"
            '''
        ),
    ]
