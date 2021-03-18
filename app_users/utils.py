import random
import string

from django.conf import settings
from django.core.mail import send_mail

from backend.errors.enums import RESTErrors, ErrorsCodes
from backend.errors.http_exception import HttpException


class EmailSender:
    def __init__(self, user, password):
        self.user = user
        self.password = password

    def send(self):
        send_mail(
            'Subject here',
            f"""Логин:{self.user.username},  Пароль:{self.password}""",
            settings.EMAIL_HOST_USER,
            [self.user.email],
            fail_silently=True,
        )


def generate_username():
    limit = random.randrange(10, 20)

    allowed = string.ascii_lowercase + string.ascii_uppercase

    return ''.join(random.choice(allowed) for i in range(limit)).lower()


def generate_password():
    limit = random.randrange(10, 20)
    allowed = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return ''.join(random.choice(allowed) for i in range(limit))


def validate_username(username):
    allowed_symbols = '-_.'
    allowed_letters = string.ascii_lowercase + string.ascii_uppercase

    allowed = allowed_symbols + allowed_letters
    if len(username) not in range(6, 20):
        raise HttpException(
            status_code=RESTErrors.CUSTOM_DETAILED_ERROR,
            detail=ErrorsCodes.USERNAME_INVALID_LENGTH.value
        )
    elif username[0] not in allowed_letters or username[-1] == '.':
        raise HttpException(
            status_code=RESTErrors.CUSTOM_DETAILED_ERROR,
            detail=ErrorsCodes.USERNAME_INVALID_SYMBOLS.value
        )

    for item in username:
        if item not in allowed:
            raise HttpException(
                status_code=RESTErrors.CUSTOM_DETAILED_ERROR,
                detail=ErrorsCodes.USERNAME_INVALID_SYMBOLS.value
            )
    return username.lower()
