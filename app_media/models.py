import uuid as uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from app_media.enums import MediaType, MediaFormat
from backend.models import BaseModel
from backend.utils import choices


class MediaModel(BaseModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    title = models.CharField(max_length=255, blank=True, null=True)
    mime_type = models.CharField(max_length=255, blank=True, null=True)

    file = models.FileField(blank=True, null=True)
    preview = models.FileField(upload_to='preview', null=True, blank=True)
    format = models.IntegerField(choices=choices(MediaFormat), blank=True, null=True, verbose_name="Тип файла")
    type = models.IntegerField(choices=choices(MediaType), blank=True, null=True, verbose_name="Принадлежность")

    width = models.IntegerField(default=None, blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    duration = models.BigIntegerField(default=None, blank=True, null=True)
    size = models.BigIntegerField(blank=True, null=True)

    owner_id = models.PositiveIntegerField(null=True, blank=True)
    owner_ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    owner_ct_name = models.CharField(max_length=255, blank=True, null=True)
    owner = GenericForeignKey(ct_field='owner_ct', fk_field='owner_id')

    def __str__(self):
        return f'{self.id} - {self.owner_ct_name} - {self.file.name}'

    class Meta:
        db_table = 'app_media'
        verbose_name = 'Медиафайл'
        verbose_name_plural = 'Медиафайлы'
