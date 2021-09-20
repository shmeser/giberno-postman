from backend.enums import IntEnumM, EnumM


class Currency(IntEnumM):
    BONUS = 0
    USD = 1
    EUR = 2
    RUB = 3


class OrderStatus(IntEnumM):
    CREATED = 0  # Создан
    COMPLETED = 1  # Успешно обработан
    CANCELED = 2  # Отменен
    FAILED = 3  # Ошибка выполнения (недостаточно средств или сбой)
    RETURNING = 4  # Возврат (средств)
    RETURNED = 5  # Возврат завершен


class OrderType(IntEnumM):
    TEST = 0
    GET_COUPON = 1  # Получение купона за очки славы (бонусов)
    WITHDRAW_BONUS_BY_VOUCHER = 2  # Вывод бонусных средств с использованием ваучера


class TransactionType(IntEnumM):
    TEST = 0
    TRANSFER = 1  # Перевод
    DEPOSIT = 2  # Пополнение
    WITHDRAWAL = 3  # Вывод
    PURCHASE = 4  # Покупка
    RETURN = 5  # Возврат
    COMMISSION = 6  # Комиссия


class TransactionStatus(IntEnumM):
    CREATED = 0  # Создана
    HOLD = 1  # Средства захолдированны
    CANCELED = 2  # Отменена (отмена холдирования)
    FAILED = 3  # Ошибка выполнения (недостаточно средств или сбой)
    COMPLETED = 4  # Успешно завершена


class TransactionKind(IntEnumM):
    PAY = 1  # Вознаграждение (зарплата)
    TAXES = 2  # Налоги
    INSURANCE = 3  # Страховка
    PENALTY = 4  # Штраф
    FRIEND_REWARD = 5  # Вознаграждение за друга


class VacancyEmployment(IntEnumM):
    PARTIAL = 0  # Частичная занятость
    FULL = 1  # Полная занятость


class WorkExperience(IntEnumM):
    NO = 0  # Без опыта - Начало пути
    INVALID = 1  # С ограниченными возможностями
    UNDERAGE = 2  # До 18 лет - несовершеннолетний
    MIDDLE = 3  # 1-3 года опыта
    STRONG = 4  # более 3 лет опыта


class ShiftStatus(IntEnumM):
    INITIAL = 0
    STARTED = 1
    CANCELED = 2
    REJECTED = 3
    COMPLETED = 4


class ShiftAppealStatus(IntEnumM):
    INITIAL = 0
    CONFIRMED = 1
    CANCELED = 2
    REJECTED = 3
    COMPLETED = 4


class AppealCancelReason(IntEnumM):
    CUSTOM = 0  # Причина будет указана самостоятельно текстом
    MISTAKE = 1  # Заявка отменена, так как создана по ошибке
    ACCIDENT = 2  # Отмена из-за непредвиденных ситуаций


class ManagerAppealCancelReason(IntEnumM):
    CUSTOM = 0  # Причина будет указана самостоятельно текстом
    MISTAKE = 1  # Заявка принята была по ошибке
    ACCIDENT = 2  # Отмена из-за непредвиденных ситуаций
    NO_PASSPORT = 3  # Нет паспорта
    WRONG_PASSPORT = 4  # Паспортные данные не верны
    NO_INN = 5  # Нет ИНН
    NO_SNILS = 6  # Нет СНИЛС
    NO_MEDICAL_BOOK = 7  # Нет медкнижки
    NO_DRIVER_LICENCE = 8  # Нет водительского удостоверения


class ManagerAppealRefuseReason(IntEnumM):
    WRONG_DOCUMENTS = 1  # Неверные документы
    UNABLE_TO_WORK = 2  # Не готов к работе


class AppealCompleteReason(IntEnumM):
    WORK_IS_DONE = 1  # Работа выполнена
    HEALTH_PROBLEM = 2  # Плохое самочувствие


class SecurityPassRefuseReason(IntEnumM):
    CUSTOM = 0  # Причина будет указана самостоятельно текстом
    NO_PASSPORT = 3  # Нет паспорта
    MANAGER_SUPPORT_NEED = 9  # Требуется помощь менеджера


class FireByManagerReason(IntEnumM):
    CUSTOM = 0  # Причина будет указана самостоятельно текстом
    INCOMPETENT = 1  # Некомпетентен - не справляется с обязанностями
    DRUNK = 2  # В состоянии алкогольного/наркотического опьянения


class ShiftWorkTime(IntEnumM):
    # Тип времени смены (время начала)
    MORNING = 0  # Утренняя
    DAY = 1  # Дневная
    EVENING = 2  # Вечерняя


class JobStatusForClient(IntEnumM):
    NO_JOB = 0  # Работы нет
    JOB_NOT_SOON = 1  # Работа нескоро
    JOB_SOON = 2  # Работа скоро
    JOB_IN_PROCESS = 3  # Работа в процессе
    WAITING_FOR_COMPLETION = 4  # Ждет завершения
    COMPLETED = 5  # Завершена
    WAITING_FOR_FIRING = 6  # Ждет увольнения
    FIRED = 7  # Уволен


class JobStatus(IntEnumM):
    JOB_SOON = 2  # Работа скоро
    JOB_IN_PROCESS = 3  # Работа в процессе
    WAITING_FOR_COMPLETION = 4  # Ждет завершения
    COMPLETED = 5  # Завершена
    WAITING_FOR_FIRING = 6  # Ждет увольнения
    FIRED = 7  # Уволен


class AchievementType(IntEnumM):
    SAME_DISTRIBUTOR_SHIFT = 1  # Успешное завершение смены в одной торговой сети
    EARLY_SHIFT = 2  # Работа в ранних сменах


class FinancesInterval(IntEnumM):
    DAY = 1
    WEEK = 2
    MONTH = 3
    YEAR = 4


class NotificationTitle(EnumM):
    MANAGER_ACCEPTED_APPEAL_TITLE = 'Отклик одобрен'
    AUTO_ACCEPTED_APPEAL_TITLE = 'Отклик одобрен автоматически'
    AUTO_REJECTED_APPEAL_TITLE = 'Отклик отклонён автоматически'
    CANCELED_APPEAL_TITLE = 'Отклик отменён'
    JOB_SOON_TITLE = 'Смена скоро начнётся'
    WAITING_COMPLETION_TITLE = 'Смена ожидает завершения'
    COMPLETED_APPEAL_TITLE = 'Смена успешно завершена'
    SECURITY_REFUSED_APPEAL_TITLE = 'Охрана не пропустила работника'
    WORKER_LEFT_SHOP_AREA_TITLE = 'Покидание территории магазина во время смены'
    WORKER_CANCELED_APPEAL_TITLE = 'Самозанятый отказался от вакансии'
    MANAGER_REJECTED_APPEAL_TITLE = 'Отклик отклонён'


class ReceiptCancelReason(IntEnumM):
    REFUND = 1  # Возврат средств
    REGISTRATION_MISTAKE = 2  # Чек сформирован ошибочно
