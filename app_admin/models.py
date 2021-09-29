import binascii
import os

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.db import models

from app_market.models import Organization
from app_users import models as users_models
from backend.models import BaseModel


class ApiKeyToken(BaseModel):
    key = models.CharField(max_length=40, primary_key=True)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(ApiKeyToken, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __unicode__(self):
        return self.key

    class Meta:
        db_table = 'app_admin__api_keys'
        verbose_name = 'API Ключ для организации'
        verbose_name_plural = 'API Ключи для организаций'


class AccessUnit(BaseModel):
    user = models.ForeignKey(users_models.UserProfile, on_delete=models.CASCADE)
    # Может быть пустым, тогда доступ ко всем подобным сущностям, которые должны быть приоритетом ниже,
    # чем разрешеннная сущность (если есть). Иначе равносильно отсутствию доступа
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    object_ct_name = models.CharField(max_length=255, blank=True, null=True)
    object = GenericForeignKey(ct_field='object_ct', fk_field='object_id')
    has_access = models.BooleanField(default=False, verbose_name='Имеет доступ')

    class Meta:
        db_table = 'app_admin__access_units'
        verbose_name = 'Объект прав доступа'
        verbose_name_plural = 'Объекты прав доступа'


class AccessRight(BaseModel):
    user = models.ForeignKey(users_models.UserProfile, on_delete=models.CASCADE)
    unit = models.OneToOneField(AccessUnit, on_delete=models.CASCADE, related_name='access_right')
    get = models.BooleanField(default=False, verbose_name='Получение')
    add = models.BooleanField(default=False, verbose_name='Добавление')
    edit = models.BooleanField(default=False, verbose_name='Редактирование')
    delete = models.BooleanField(default=False, verbose_name='Удаление')

    class Meta:
        db_table = 'app_admin__access_rights'
        verbose_name = 'Право доступа пользователя'
        verbose_name_plural = 'Права доступа пользователей'


'''
    Зависимые сущности - низшие ограничиваются высшими (напр., вакансии можно редактировать если есть доступ к магазинам, или к торговым сетям. (либо если есть конкретный запрет на что-то))
    Structure
    Distributor
    Shop
    
    Vacancy
'''
