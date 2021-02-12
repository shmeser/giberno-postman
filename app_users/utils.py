from django.conf import settings
from django.core.mail import send_mail


class EmailSender:
    def __init__(self, user):
        self.email = user.email

    def send(self):
        send_mail(
            'Subject here',
            'Here is the message.',
            settings.EMAIL_HOST_USER,
            [self.email],
            fail_silently=False,
        )
