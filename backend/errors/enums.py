from backend.enums import EnumM, IntEnumM


class RESTErrors(IntEnumM):
    BAD_REQUEST = 400
    NOT_AUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CUSTOM_DETAILED_ERROR = 499
    INTERNAL_SERVER_ERROR = 500


class ErrorsCodes(EnumM):
    METHOD_NOT_FOUND = 'Метод не найден'
    SOCIAL_ALREADY_IN_USE = 'Данным способом уже зарегистрирован другой пользователь'
    PROFILE_NOT_FILLED = 'Профиль не заполнен'
    PHONE_IS_USED = 'Этот номер телефона уже занят'
    EMAIL_IS_USED = 'Этот email уже занят'
    ALREADY_REGISTERED_WITH_OTHER_ROLE = 'Данным способом уже зарегистрирован пользователь с другой ролью'
    VALIDATION_ERROR = 'Ошибка валидации'
    EMPTY_REQUIRED_FIELDS = 'Не все обязательные поля отправлены'
    UNSUPPORTED_FILE_FORMAT = 'Неподдерживаемый формат файла'
    DELETING_REG_SOCIAL = 'Нельзя отвязать соцсеть, через которую был создан аккаунт'

    INVALID_COORDS = 'Некорректные географические координаты'
    INVALID_DATE_RANGE = 'Некорректный диапазон дат'

    USERNAME_WRONG = 'Неверный логин'
    USERNAME_TAKEN = 'Логин занят'

    USERNAME_INVALID_SYMBOLS = 'Логин должен начинаться с буквы и не может заканчиваться точкой. Допустимы только латинские буквы, цифры, символы тире (-), подчеркивания (_) и точки (.)'
    USERNAME_INVALID_LENGTH = 'Логин должен состоять не менее чем из 6 символов и не более чем из 20 символов'

    WRONG_PASSWORD = 'Неверный пароль'

    APPEAL_EXISTS = 'Вы уже откликнулись на эту смену'
    APPEALS_LIMIT_REACHED = 'Слишком много откликов на смены с пересекающимся временем'
    SHIFT_WITHOUT_TIME = 'У cмены нет времени начала и окончания'
    SHIFT_OVERDUE = 'Просроченная смена'

    VACANCY_OR_SHOP_CHAT_IS_BLOCKED = 'Вы были заблокированы и не можете подать заявку на эту вакансию'

    APPEAL_ALREADY_COMPLETED = 'Эта смена уже завершена'
    APPEAL_ALREADY_CANCELLED = 'Эта смена уже закрыта'
    INCONVENIENT_JOB_STATUS = 'Для выполнения данного действия статус работы должен быть другим'

    TOO_MANY_REVIEWS = 'Слишком много отзывов'

    NO_SUITABLE_COUPON = 'Нет подходящего купона для данной операции'
    YOU_HAVE_THIS_COUPON_ALREADY = 'Вы уже получали такой купон'

    NOT_ENOUGH_BONUS_BALANCE = 'Недостаточно бонусов для данной операции'

    CARD_ALREADY_USED_IN_OTHER_ACCOUNT = 'Карта уже используется в другом аккаунте'

    MAX_PREFERRED_PRIZES_AMOUNT_EXCEEDED = 'Превышено число предпочитаемых товаров данного уровня'

    NO_ACTIVE_INSURANCE = 'Нет оформленной страховки'

    PRIZE_CARD_WAS_NOT_BEEN_ISSUED = 'Новая карточка Вам еще не выдавалась'


class SocketErrors(IntEnumM):
    # Диапазон 3000-4999
    BAD_REQUEST = 4000
    NOT_AUTHORIZED = 4001
    FORBIDDEN = 4003
    NOT_FOUND = 4004
    CUSTOM_DETAILED_ERROR = 4099
