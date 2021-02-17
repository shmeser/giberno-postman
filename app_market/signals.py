from django.db.models.signals import pre_save
from django.dispatch import receiver

from app_market.models import Vacancy


@receiver(pre_save, sender=Vacancy)
def set_timezone_to_vacancy(sender, instance, **kwargs):
    # Устанавливаем для вакансии часовой пояс из города, в котором она находится
    instance.timezone = instance.shop.city.timezone or 'Europe/Moscow'
