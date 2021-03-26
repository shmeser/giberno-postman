from backend.enums import IntEnumM, EnumM


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


class NotificationChannelFromAndroid8(EnumM):
    # Канал уведомлений для пушей на Android 8 и новее без звука и со звуком
    # Для каждого значения из NotificationType по 2 варианта

    # Системные уведомления
    SYSTEM = 'system_channel'
    SYSTEM_SOUNDLESS = 'system_channel_soundless'  # без звука


class NotificationAction(IntEnumM):
    # Для открытия нужного экрана в приложении
    APP = 0  # Главный экран в приложении
    VACANCY = 1  # Вакансия


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
    LEAVED_SHOP_AREA = 9
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
