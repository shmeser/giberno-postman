from backend.enums import IntEnumM, EnumM
from django.db import models


class Gender(IntEnumM):
    FEMALE = 0
    MALE = 1


class Status(IntEnumM):
    NEW = 0
    ACTIVE = 1
    BLOCKED = 2


class AccountType(IntEnumM):
    ADMIN = 0
    MANAGER = 1
    SECURITY = 2
    SELF_EMPLOYED = 3


class LanguageProficiency(IntEnumM):
    BEGINNER = 0
    ELEMENTARY = 1
    INTERMEDIATE = 2
    UPPER_INTERMEDIATE = 3
    ADVANCED = 4
    PROFICIENCY = 5


class NotificationType(IntEnumM):
    # Для настроек получения уведомлений
    SYSTEM = 0  # Системные уведомления
    CHAT = 1  # Сообщения в чатах
    NALOG = 2  # Сообщения от налоговой


class NotificationChannelFromAndroid8(EnumM):
    """
        # Для каждого значения из NotificationType по 2 варианта
        # Канал уведомлений для пушей на Android 8 и новее без звука и со звуком
        # ВАЖНО ключ значения должен быть таким же для "звука", а "без звука" - + "_SOUNDLESS"
    """
    # Системные уведомления
    SYSTEM = 'system_channel'
    SYSTEM_SOUNDLESS = 'system_channel_soundless'  # без звука

    # Сообщения в чатах
    CHAT = 'chat_channel'
    CHAT_SOUNDLESS = 'chat_channel_soundless'  # без звука

    # Сообщения от налоговой
    NALOG = 'nalog_channel'
    NALOG_SOUNDLESS = 'nalog_channel_soundless'  # без звука


class NotificationAction(IntEnumM):
    # Для открытия нужного экрана в приложении
    APP = 0  # Главный экран в приложении
    VACANCY = 1  # Вакансия
    SHIFT = 2  # Смена
    SHOP = 3  # Магазин
    DISTRIBUTOR = 4  # Торговая сеть
    USER = 5  # Пользователь
    CHAT = 6  # Чат


class NotificationIcon(IntEnumM):
    DEFAULT = 0
    REQUEST_APPROVED = 1
    REQUEST_DECLINED = 2
    MONEY_RECEIVED = 3
    REWARD_RECEIVED = 4
    DOCS_APPROVED = 5
    DOCS_DECLINED = 6
    SHIFT_AVAILABLE = 7
    SHIFT_START_SOON = 8
    LEFT_SHOP_AREA = 9
    VACANCY_APPROVED = 10
    VACANCY_DECLINED = 11
    WORKER_CANCELED_VACANCY = 12
    SECURITY_CALL = 13
    SECURITY_CANCELLATION_REASON = 14


class Education(IntEnumM):
    SCHOOL = 0  # Общее (школа)
    COLLEGE = 1  # Профессиональное-техническое (колледж, техникум)
    UNIVERSITY = 2  # Высшее (университет)


class DocumentType(IntEnumM):
    OTHER = 0
    PASSPORT = 1
    INN = 2
    SNILS = 3
    MEDICAL_BOOK = 4
    DRIVER_LICENCE = 5
    VACCINATION_CERTIFICATE = 6  # Сертификат о вакцинации
    VISA = 7  # Виза
    RESIDENT_CARD = 8  # Вид на жительство
    MIGRATION_CARD = 9  # Миграционная карта


REQUIRED_DOCS_FOR_CHOICES = [
    (DocumentType.PASSPORT.value, 'Паспорт'),
    (DocumentType.INN.value, 'ИНН'),
    (DocumentType.SNILS.value, 'СНИЛС'),
    (DocumentType.MEDICAL_BOOK.value, 'Медкнижка'),
    (DocumentType.DRIVER_LICENCE.value, 'Водительское удостоверение'),
]

REQUIRED_DOCS_DICT = {
    DocumentType.PASSPORT: 'Паспорт',
    DocumentType.INN: 'ИНН',
    DocumentType.SNILS: 'СНИЛС',
    DocumentType.MEDICAL_BOOK: 'Медкнижка',
    DocumentType.DRIVER_LICENCE: 'Водительское удостоверение',
}


class CardType(IntEnumM):
    DEBIT = 1  # Дебетовая
    CREDIT = 2  # Кредитная
    PREPAID = 3  # Предоплаченная (виртуальная и т.д.)


class CardPaymentNetwork(IntEnumM):
    UNKNOWN = 0
    VISA = 1
    MASTERCARD = 2
    MIR = 3


class NalogUserStatus(models.IntegerChoices):
    NOT_SELF_EMPLOYED = 0, 'Пользователь не является самозанятым'
    NOT_ATTACHED_TO_A_PARTNER = 1, 'Пользователь является самозанятым, но не привязан к партнеру'
    ATTACHED_TO_A_PARTNER = 2, 'Пользователь самозанятый и привязан к партнеру'
    UNKNOWN = 3, 'Неизвестный статус, возможна ошибка в данных'
