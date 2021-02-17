from django.conf import settings
from django.core.mail import send_mail


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
