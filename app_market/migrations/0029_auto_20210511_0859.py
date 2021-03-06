# Generated by Django 3.1.4 on 2021-05-11 05:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_media', '0012_auto_20210429_1601'),
        ('app_market', '0028_auto_20210428_1916'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distributordocument',
            name='document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_distributor_documents', to='app_media.mediamodel'),
        ),
        migrations.AlterField(
            model_name='globaldocument',
            name='document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_global_documents', to='app_media.mediamodel'),
        ),
        migrations.AlterField(
            model_name='vacancydocument',
            name='document',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_vacancy_documents', to='app_media.mediamodel'),
        ),
    ]
