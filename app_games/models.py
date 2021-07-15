from django.contrib.gis.db import models

from app_market.enums import Currency
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
    price = models.PositiveIntegerField(null=True, blank=True, verbose_name='Цена в осколках')
    real_price_ = models.PositiveIntegerField(null=True, blank=True, verbose_name='Реальная цена')
    real_price_currency = models.PositiveIntegerField(choices=choices(Currency), default=Currency.RUB.value, verbose_name='Валюта реальной цены')
    categories = models.ManyToManyField(GoodsCategory, through='PrizeCategory', blank=True, related_name='prizes')

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
