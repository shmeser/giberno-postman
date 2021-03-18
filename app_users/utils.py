from django.conf import settings
from django.core.mail import send_mail
from loguru import logger


class EmailSender:
    def __init__(self, user, password):
        self.user = user
        self.password = password

    def send(self):
        try:
            send_mail(
                subject='Subject here',
                message=f"Логин:{self.user.username},  Пароль:{self.password}",
                from_email=f'GIBERNO Admin {settings.EMAIL_HOST_USER}',
                recipient_list=[self.user.email],
                auth_user=settings.EMAIL_HOST_USER,
                auth_password=settings.EMAIL_HOST_PASSWORD,
                fail_silently=False,
            )
        except Exception as e:
            logger.error(e)
