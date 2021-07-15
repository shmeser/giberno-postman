from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.gis.db import models

from app_games.enums import Grade, TaskPeriod, TaskType
from app_market.enums import Currency
from app_media.models import MediaModel
from app_users.models import UserProfile
from backend.models import BaseModel
from backend.utils import choices


class GoodsCategory(BaseModel):
    title = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=2048, null=True, blank=True)

    def __str__(self):
        return f'{self.title}'

    class Meta:
        db_table = 'app_games__goods_categories'
        verbose_name = 'Категория товаров'
        verbose_name_plural = 'Категории товаров'


class Prize(BaseModel):
    name = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=1024, null=True, blank=True)
    count = models.PositiveIntegerField(default=1, verbose_name='Исходное количество товара')
    price = models.PositiveIntegerField(null=True, blank=True, verbose_name='Цена в осколках')
    grade = models.PositiveIntegerField(
        choices=choices(Grade), default=Grade.DEFAULT.value, verbose_name='Уровень товара'
    )

    real_price_ = models.PositiveIntegerField(null=True, blank=True, verbose_name='Реальная цена')
    real_price_currency = models.PositiveIntegerField(
        choices=choices(Currency), default=Currency.RUB.value, verbose_name='Валюта реальной цены'
    )
    categories = models.ManyToManyField(GoodsCategory, through='PrizeCategory', blank=True, related_name='prizes')
    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_games__prizes'
        verbose_name = 'Приз'
        verbose_name_plural = 'Призы'


class PrizeCategory(BaseModel):
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)
    category = models.ForeignKey(GoodsCategory, on_delete=models.CASCADE)

    class Meta:
        db_table = 'app_games__prize_category'
        verbose_name = 'Категория приза'
        verbose_name_plural = 'Категории призов'


class PrizeCard(BaseModel):
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)
    value = models.PositiveIntegerField(null=True, blank=True, verbose_name='Номинал в осколках')
    grade = models.PositiveIntegerField(
        choices=choices(Grade), default=Grade.DEFAULT.value, verbose_name='Уровень карточки'
    )

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    class Meta:
        db_table = 'app_games__prize_cards'
        verbose_name = 'Призовая карточка'
        verbose_name_plural = 'Призовые карточки'


class UserFavouritePrize(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)

    class Meta:
        db_table = 'app_games__user_favourite_prizes'
        verbose_name = 'Приоритетный приз пользователя'
        verbose_name_plural = 'Приоритетные призы пользователей'


class UserPrizeProgress(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)

    class Meta:
        db_table = 'app_games__user_prize_progress'
        verbose_name = 'Прогресс пользователя по призу'
        verbose_name_plural = 'Прогресс пользователей по призам'


class Task(BaseModel):
    name = models.CharField(max_length=128, null=True, blank=True)
    description = models.CharField(max_length=3072, null=True, blank=True)
    bonus_value = models.PositiveIntegerField(default=1, verbose_name='Баллов за выполнение')
    period = models.PositiveIntegerField(
        choices=choices(TaskPeriod), default=TaskPeriod.DAILY.value, verbose_name='Период задачи'
    )
    type = models.PositiveIntegerField(
        choices=choices(TaskType), default=TaskType.COMMON.value, verbose_name='Тип задачи'
    )

    media = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    def __str__(self):
        return f'{self.name}'

    class Meta:
        db_table = 'app_games__tasks'
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'


class UserTask(BaseModel):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.id}'

    class Meta:
        db_table = 'app_games__task_user'
        verbose_name = 'Задание пользователя'
        verbose_name_plural = 'Задания пользователей'
