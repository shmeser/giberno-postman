from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('app_geo', '0006_auto_20210111_1352'),
    ]
    operations = [
        TrigramExtension(),
    ]
