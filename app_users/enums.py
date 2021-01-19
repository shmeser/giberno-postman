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


class NotificationAction(IntEnumM):
    # Для открытия нужного экрана в приложении
    APP = 0  # Главный экран в приложении
    VACANCY = 1  # Вакансия


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
