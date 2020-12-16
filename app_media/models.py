import uuid as uuid

from django.db import models

from app_media.enums import MediaType, MediaFormat
from backend.models import BaseModel
from backend.utils import choices


class MediaModel(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    owner_id = models.IntegerField(blank=True, null=True)
    owner_content_type_id = models.IntegerField(blank=True, null=True)
    owner_content_type = models.CharField(max_length=255, blank=True, null=True)

    title = models.CharField(max_length=255, blank=True, null=True)

    file = models.FileField(upload_to='files/media', blank=True, null=True)
    preview = models.FileField(upload_to='files/media', null=True, blank=True)
    format = models.IntegerField(choices=choices(MediaFormat), blank=True, null=True, verbose_name="Тип файла")
    type = models.IntegerField(choices=choices(MediaType), blank=True, null=True, verbose_name="Принадлежность")

    width = models.IntegerField(default=None, blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    duration = models.BigIntegerField(default=None, blank=True, null=True)
    bytes = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f'{self.id} - {self.owner_content_type} - {self.file.name}'

    class Meta:
        db_table = 'app_media'
        verbose_name = 'Медиафайл'
        verbose_name_plural = 'Медиафайлы'
