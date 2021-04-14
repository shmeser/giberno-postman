from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField

from app_bot.enums import ChatterBotIntentCode
from backend.models import BaseModel
from backend.utils import choices


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
        return f'{self.username or self.title}'

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


class SupportIntentsManager(models.Manager):
    def get_queryset(self):
        # TODO
        return super().get_queryset().all().prefetch_related('requests', 'responses')


class CommonIntentsManager(models.Manager):
    def get_queryset(self):
        # TODO
        return super().get_queryset().all().prefetch_related('requests', 'responses')


class Intent(BaseModel):
    code = models.IntegerField(choices=choices(ChatterBotIntentCode), null=True, blank=True)
    topic = models.CharField(max_length=255, null=True, blank=True)

    support = SupportIntentsManager()  # Темы для поддержки
    common = CommonIntentsManager()  # Темы для общих разговоров

    def __str__(self):
        return f'{self.topic}'

    class Meta:
        db_table = 'app_bot__intents'
        verbose_name = 'Тема разговора для бота'
        verbose_name_plural = 'Темы разговоров для бота'


class IntentRequest(BaseModel):
    intent = models.ForeignKey(Intent, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.intent.id}:{self.intent.topic}|{self.text}'

    class Meta:
        db_table = 'app_bot__intents_requests'
        verbose_name = 'Вариант запроса для темы'
        verbose_name_plural = 'Варианты запросов для темы'


class IntentResponse(BaseModel):
    intent = models.ForeignKey(Intent, on_delete=models.SET_NULL, null=True, blank=True, related_name='responses')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.intent.id}:{self.intent.topic}|{self.text}'

    class Meta:
        db_table = 'app_bot__intents_responses'
        verbose_name = 'Вариант ответа для теме'
        verbose_name_plural = 'Варианты ответов для теме'
