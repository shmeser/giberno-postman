from django.db.models.signals import pre_save
from django.dispatch import receiver

from app_market.models import Vacancy


@receiver(pre_save, sender=Vacancy)
def set_timezone_to_vacancy(sender, instance, **kwargs):
    # Устанавливаем для вакансии часовой пояс из города, в котором она находится
    instance.timezone = instance.shop.city.timezone \
        if instance.shop.city and instance.shop.city.timezone else 'Europe/Moscow'
    # Поменял чтоб код не ломался при seed когда нет городов в базе данных и instance.shop.city == None
