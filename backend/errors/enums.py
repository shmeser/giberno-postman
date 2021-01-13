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


class SocketErrors(IntEnumM):
    USER_NOT_FOUND = 1004
