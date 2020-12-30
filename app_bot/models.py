from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from backend.models import BaseModel


class BotChat(BaseModel):
    chat_id = models.BigIntegerField()
    type = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)

    approved = models.BooleanField(default=False)

    notification_types = ArrayField(models.CharField(max_length=32), size=10, blank=True, null=True)

    def __str__(self):
        return f'{self.username}'

    class Meta:
        db_table = 'app_bot__chats'
        verbose_name = 'Чат телеграм-бота'
        verbose_name_plural = 'Чаты телеграм-бота'


class BotMessage(BaseModel):
    chat = models.ForeignKey(BotChat, on_delete=models.SET_NULL, blank=True, null=True)
    message_id = models.IntegerField(blank=True, null=True)
    chat_type = models.CharField(max_length=255, blank=True, null=True)
    from_id = models.IntegerField(blank=True, null=True)
    is_bot = models.BooleanField(default=False)
    title = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    language_code = models.CharField(max_length=16, blank=True, null=True)
    date = models.DateTimeField(null=True, blank=True)
    text = models.CharField(max_length=4096, blank=True, null=True)

    def __str__(self):
        return f'{self.text}'

    class Meta:
        db_table = 'app_bot__messages'
        verbose_name = 'Сообщение чата телеграм-бота'
        verbose_name_plural = 'Сообщения чатов телеграм-бота'
