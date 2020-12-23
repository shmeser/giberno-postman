from django.db.models.signals import post_delete
from django.dispatch import receiver

from app_media.models import MediaModel
from backend.utils import remove_file_from_server


@receiver(post_delete, sender=MediaModel)
def remove_file_from_disk(sender, instance, **kwargs):
    remove_file_from_server(instance.file.name)
    remove_file_from_server(instance.preview.name)
