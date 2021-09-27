# Generated by Django 3.1.4 on 2021-09-27 12:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('appcraft_nalog_sdk', '0026_nalogincomerequestmodel_cancel_message_id'),
        ('app_market', '0071_organization'),
    ]

    operations = [
        migrations.RenameField(
            model_name='organization',
            old_name='address',
            new_name='address_legal',
        ),
        migrations.RenameField(
            model_name='organization',
            old_name='inn',
            new_name='legal_inn',
        ),
        migrations.RenameField(
            model_name='organization',
            old_name='kpp',
            new_name='legal_kpp',
        ),
        migrations.RenameField(
            model_name='organization',
            old_name='ogrn',
            new_name='legal_ogrn',
        ),
        migrations.AddField(
            model_name='organization',
            name='address_post',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='bank_account',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='bank_bik',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='bank_inn',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='bank_korr_account',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='bank_kpp',
            field=models.CharField(blank=True, max_length=12, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='bank_name',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='legal_form',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='legal_form_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='organization',
            name='legal_ogrn_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transaction',
            name='receipt',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='appcraft_nalog_sdk.nalogincomerequestmodel'),
        ),
    ]
