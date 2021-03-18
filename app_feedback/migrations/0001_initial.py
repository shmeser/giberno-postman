# Generated by Django 3.1.4 on 2021-02-19 07:36

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('owner_ct_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Имя модели - владельца')),
                ('target_ct_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Имя модели - конечной цели')),
                ('owner_id', models.PositiveIntegerField(blank=True, null=True)),
                ('target_id', models.PositiveIntegerField(blank=True, null=True)),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('text', models.TextField(blank=True, max_length=4096, null=True, verbose_name='Текст сообщения')),
                ('value', models.FloatField(blank=True, null=True, verbose_name='Величина оценки')),
                ('owner_ct', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review_owner_ct', to='contenttypes.contenttype')),
                ('target_ct', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review_target_ct', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Отзыв',
                'verbose_name_plural': 'Отзывы',
                'db_table': 'app_feedback__reviews',
            },
        ),
        migrations.CreateModel(
            name='Like',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted', models.BooleanField(default=False)),
                ('owner_ct_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Имя модели - владельца')),
                ('target_ct_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Имя модели - конечной цели')),
                ('owner_id', models.PositiveIntegerField(blank=True, null=True)),
                ('target_id', models.PositiveIntegerField(blank=True, null=True)),
                ('owner_ct', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='like_owner_ct', to='contenttypes.contenttype')),
                ('target_ct', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='like_target_ct', to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name': 'Лайк',
                'verbose_name_plural': 'Лайки',
                'db_table': 'app_feedback__likes',
            },
        ),
    ]
