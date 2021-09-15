from django.utils import timezone
from loguru import logger

from appcraft_nalog_sdk.models import NalogUser
from appcraft_nalog_sdk.sdk import NalogSdk
from giberno.celery import app


@app.task(bind=True)
def update_processing_statuses(self):
    """
    Обновить все запросы по message_id, у которых статус В процессе
    :param self:
    :return:
    """
    try:
        NalogSdk().update_processing_statuses()
    except Exception as ex:
        logger.debug(ex)
        raise self.retry(exc=ex)


@app.task(bind=True)
def update_offline_keys(self):
    """
    Обновить все оффлайн ключи для регистрации дохода
    :param self:
    :return:
    """
    try:
        NalogSdk().update_keys()
    except Exception as ex:
        logger.debug(ex)
        raise self.retry(exc=ex)


@app.task(bind=True)
def get_newly_unbound_taxpayers_request(self):
    """
    Запросить всех отвязанных от партнера людей за прошедшие сутки
    :param self:
    :return:
    """
    try:
        NalogSdk().get_newly_unbound_taxpayers_request(
            from_date=(timezone.now() - timezone.timedelta(days=1)).isoformat(),
            to_date=(timezone.now() + timezone.timedelta(days=1)).isoformat(),
            offset=0
        )
    except Exception as ex:
        logger.debug(ex)
        raise self.retry(exc=ex)


@app.task(bind=True)
def get_income_request(self):
    """
    Запросить все регистрации доходов за прошедшие сутки
    :param self:
    :return:
    """
    try:
        for user in NalogUser.objects.all():
            NalogSdk().get_income_request(
                user.inn,
                from_date=(timezone.now() - timezone.timedelta(days=1)).isoformat(),
                to_date=(timezone.now() + timezone.timedelta(days=1)).isoformat(),
            )
    except Exception as ex:
        logger.debug(ex)
        raise self.retry(exc=ex)


@app.task(bind=True)
def get_granted_permissions_request(self):
    """
    Обновить статусы и разрешения всех самозанятых
    :param self:
    :return:
    """
    try:
        for user in NalogUser.objects.all():
            NalogSdk().get_granted_permissions_request(
                user.inn
            )
    except Exception as ex:
        logger.debug(ex)
        raise self.retry(exc=ex)


@app.task(bind=True)
def get_payment_documents_request(self):
    """
    Получение платежных документов для уплаты налогов
    :param self:
    :return:
    """
    try:
        NalogSdk().get_payment_documents_request([inn[0] for inn in NalogUser.objects.values_list('inn')])
    except Exception as ex:
        logger.debug(ex)
        raise self.retry(exc=ex)
