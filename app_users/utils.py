import random
import string

from django.conf import settings
from django.core.mail import send_mail
from loguru import logger

from backend.entity import Error
from backend.errors.enums import ErrorsCodes
from backend.errors.http_exceptions import CustomException


class EmailSender:
    def __init__(self, user, password):
        self.user = user
        self.password = password

    def send(self, subject='Новое письмо'):
        try:
            send_mail(
                subject=subject,
                message=f"Логин:{self.user.username},  Пароль:{self.password}",
                from_email=f'GIBERNO Admin {settings.EMAIL_HOST_USER}',
                recipient_list=[self.user.email],
                auth_user=settings.EMAIL_HOST_USER,
                auth_password=settings.EMAIL_HOST_PASSWORD,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(e)


def generate_username():
    limit = random.randrange(10, 20)

    allowed = string.ascii_lowercase + string.ascii_uppercase

    return ''.join(random.choice(allowed) for _ in range(limit)).lower()


def generate_password():
    limit = random.randrange(10, 20)
    allowed = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(allowed) for _ in range(limit))


# Требования к логину:
# логин должен начинаться с буквы и состоять не менее чем из 6 символов и не более чем из 20 символов;
# при создании логина можно использовать латинские буквы, цифры, символы тире (-), подчеркивания (_) и точки (.),
# остальные символы недопустимы;
# пробел в логине недопустим;
# логин не может заканчиваться точкой.
# Логин можно вводить в любом регистре (PETROV, petrov и PeTrOv - один и тот же логин).


def validate_username(username):
    allowed_symbols = '-_.'
    allowed_letters = string.ascii_lowercase + string.ascii_uppercase + string.digits

    allowed = allowed_symbols + allowed_letters
    if len(username) not in range(6, 20):
        raise CustomException(errors=[
            dict(Error(ErrorsCodes.USERNAME_INVALID_LENGTH))
        ])
    elif username[0] not in allowed_letters or username[0] in string.digits or username[-1] == '.':
        raise CustomException(errors=[
            dict(Error(ErrorsCodes.USERNAME_INVALID_SYMBOLS))
        ])

    for item in username:
        if item not in allowed:
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.USERNAME_INVALID_SYMBOLS))
            ])
    return username.lower()
