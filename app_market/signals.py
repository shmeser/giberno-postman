from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from app_market.models import Vacancy, Shop
from backend.tasks import shops_update_static_map


@receiver(pre_save, sender=Vacancy)
def set_timezone_to_vacancy(sender, instance, **kwargs):
    # Устанавливаем для вакансии часовой пояс из города, в котором она находится
    instance.timezone = instance.shop.city.timezone \
        if instance.shop.city and instance.shop.city.timezone else 'Europe/Moscow'
    # Поменял чтоб код не ломался при seed когда нет городов в базе данных и instance.shop.city == None


@receiver(post_save, sender=Shop)
def update_static_map(sender, instance: Shop, created, **kwargs):
    # Генерируем картинку статической карты
    shops_update_static_map.s(shops_ids=[instance.id]).apply_async()
