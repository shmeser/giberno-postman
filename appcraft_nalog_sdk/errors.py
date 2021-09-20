import logging
from enum import Enum, IntEnum

from rest_framework.exceptions import APIException

from appcraft_nalog_sdk.enums import NalogUserStatus


class NalogErrorEnum(Enum):
    INTERNAL_ERROR = 'Внутренняя ошибка ПП НПД'
    REQUEST_VALIDATION_ERROR = 'Ошибка парсинга запроса'
    PARTNER_DENY = 'Партнеру отказано в осуществлении операций'
    TAXPAYER_UNREGISTERED = 'НП НПД снят с учета или не обнаружен'
    TAXPAYER_UNBOUND = 'Пользователь не привязан к Партнеру'
    TAXPAYER_ALREADY_BOUND = 'НП НПД уже привязан'
    DUPLICATE = 'Такой доход уже был зарегистрирован'
    PERMISSION_NOT_GRANTED = 'У Партнера нет прав на регистрацию дохода'
    ALREADY_DELETED = 'Чек с таким ID уже сторнирован'

    # скорее всего не надо
    RECEPT_ID_NOT_FOUND = 'Чек с таким ID не зарегистрирован'
    INVALID_HASH = 'Чек не может быть принят, так как у него не корректный фискальный признак'
    INVALID_SEQUENCE = 'Для получения фискального признака был использован не валидный номер последовательности'


class ErrorEnum(IntEnum):
    RECEIPT_ID_NOT_FOUND = 597
    ORDER_ID_NOT_FOUND = 598
    MESSAGE_ID_NOT_FOUND = 599


class NalogException(Exception):
    def __init__(self, reason=None):
        logger = logging.getLogger(__name__)
        logger.error(reason)
        self.detail = reason


# не найдена заявка на привязку пользователя к партнеру
class OrderIdNotFoundException(APIException):
    def __init__(self):
        self.detail = ErrorEnum.ORDER_ID_NOT_FOUND.name
        self.status_code = ErrorEnum.ORDER_ID_NOT_FOUND.value


# не найден запрос с текущим message_id или запрос слишком старый
class MessageIdNotFoundException(APIException):
    def __init__(self):
        self.detail = ErrorEnum.MESSAGE_ID_NOT_FOUND.name
        self.status_code = ErrorEnum.MESSAGE_ID_NOT_FOUND.value


# чек с данным id не найден
class ReceiptIdNotFoundException(APIException):
    def __init__(self):
        self.detail = ErrorEnum.RECEIPT_ID_NOT_FOUND.name
        self.status_code = ErrorEnum.RECEIPT_ID_NOT_FOUND.value


class InternalErrorException(NalogException):
    pass


class RequestValidationException(NalogException):
    pass


class PartnerDenyException(NalogException):
    pass


class TaxpayerUnregisteredException(NalogException):
    pass


class TaxpayerUnboundException(NalogException):
    pass


class TaxpayerAlreadyBoundException(NalogException):
    pass


class DuplicateException(NalogException):
    pass


class PermissionNotGrantedException(NalogException):
    pass


class AlreadyDeletedException(NalogException):
    pass


class InvalidHashException(NalogException):
    pass


class ErrorController:
    @staticmethod
    def check_error(response, user=None) -> None:
        """
        Проверка на наличие ошибок внутри ответа
        :param response: результат запроса GetMessage
        :param user: налоговый пользователь, если есть

        :return: один из значений ErrorEnum или None
        """

        if 'SmzPlatformError' not in response:
            return

        error = NalogErrorEnum[
            response['SmzPlatformError']['Code']]
        message = response['SmzPlatformError'][
            'Message']

        if error == NalogErrorEnum.INTERNAL_ERROR:
            raise InternalErrorException(reason=message)

        if error == NalogErrorEnum.REQUEST_VALIDATION_ERROR:
            raise RequestValidationException(reason=message)

        if error == NalogErrorEnum.PARTNER_DENY:
            raise PartnerDenyException(reason=message)

        if error == NalogErrorEnum.TAXPAYER_UNREGISTERED:
            user.update_status(NalogUserStatus.NOT_SELF_EMPLOYED)
            raise TaxpayerUnregisteredException(reason=message)

        if error == NalogErrorEnum.TAXPAYER_UNBOUND:
            user.update_status(NalogUserStatus.NOT_ATTACHED_TO_A_PARTNER)
            raise TaxpayerUnboundException(reason=message)

        if error == NalogErrorEnum.TAXPAYER_ALREADY_BOUND:
            user.update_status(NalogUserStatus.ATTACHED_TO_A_PARTNER)
            raise TaxpayerAlreadyBoundException(reason=message)

        if error == NalogErrorEnum.DUPLICATE:
            raise DuplicateException(reason=message)

        if error == NalogErrorEnum.PERMISSION_NOT_GRANTED:
            user.update_tax_payment(False)
            raise PermissionNotGrantedException(reason=message)

        if error == NalogErrorEnum.ALREADY_DELETED:
            raise AlreadyDeletedException(reason=message)

        if error == NalogErrorEnum.INVALID_HASH:
            raise InvalidHashException(reason=message)
