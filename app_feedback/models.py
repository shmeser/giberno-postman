import uuid as uuid

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

from app_geo.models import Region
from app_media.models import MediaModel
from backend.models import GenericSourceTargetBase


class Review(GenericSourceTargetBase):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)

    text = models.TextField(max_length=4096, blank=True, null=True, verbose_name="Текст сообщения")
    value = models.FloatField(blank=True, null=True, verbose_name="Величина оценки")

    attachment = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    owner_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='review_owner_ct'
    )
    target_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='review_target_ct'
    )

    region = models.ForeignKey(to=Region, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.id} - {self.owner_ct_name}=>{self.target_ct_name} - {self.text}'

    class Meta:
        db_table = 'app_feedback__reviews'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'


class Like(GenericSourceTargetBase):
    owner_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='like_owner_ct'
    )
    target_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='like_target_ct'
    )

    def __str__(self):
        return f'{self.id} - {self.owner_ct_name}=>{self.target_ct_name}'

    class Meta:
        db_table = 'app_feedback__likes'
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'
