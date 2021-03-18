from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    def get_nullable_fields(self):
        fields = self._meta.concrete_fields
        return [f.column for f in fields if getattr(f, 'blank', True) and getattr(f, 'null', True)]

    class Meta:
        abstract = True


class GenericSourceTargetBase(BaseModel):
    owner_ct_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя модели - владельца')
    target_ct_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя модели - конечной цели')

    # Generic Relation base для автора
    owner_id = models.PositiveIntegerField(null=True, blank=True)
    owner_ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='owner_ct')
    owner = GenericForeignKey(ct_field='owner_ct', fk_field='owner_id')

    # Generic Relation base для конечной цели
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='target_ct'
    )
    target = GenericForeignKey(ct_field='target_ct', fk_field='target_id')

    class Meta:
        abstract = True
