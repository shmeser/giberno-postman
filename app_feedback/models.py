import uuid as uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models

from app_media.models import MediaModel
from backend.models import GenericSourceTargetBase


class Comment(GenericSourceTargetBase):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    text = models.TextField(max_length=4096, blank=True, null=True, verbose_name="Текст сообщения")
    attachment = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    def __str__(self):
        return f'{self.id} - {self.owner_ct_name}=>{self.target_ct_name} - {self.text}'

    class Meta:
        db_table = 'app_feedback__comments'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'


class Rate(GenericSourceTargetBase):
    value = models.FloatField(blank=True, null=True, verbose_name="Величина оценки")

    def __str__(self):
        return f'{self.id} - {self.owner_ct_name}=>{self.target_ct_name} - {self.value}'

    class Meta:
        db_table = 'app_feedback__rates'
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'


class Like(GenericSourceTargetBase):
    def __str__(self):
        return f'{self.id} - {self.owner_ct_name}=>{self.target_ct_name}'

    class Meta:
        db_table = 'app_feedback__likes'
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
