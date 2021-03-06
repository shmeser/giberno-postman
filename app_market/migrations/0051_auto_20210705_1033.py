# Generated by Django 3.1.4 on 2021-07-05 07:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('app_market', '0050_auto_20210705_1030'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='from_ct',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='from_ct', to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='from_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='to_ct',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='to_ct', to='contenttypes.contenttype'),
        ),
        migrations.AddField(
            model_name='transaction',
            name='to_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
