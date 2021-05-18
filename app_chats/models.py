import uuid as uuid

from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from app_bot.enums import ChatterBotStates
from app_chats.enums import ChatMessageType, ChatManagerState, ChatMessageIconType
from app_media.models import MediaModel
from app_users.models import UserProfile
from backend.models import GenericSourceTargetBase, BaseModel
from backend.utils import choices


class Chat(BaseModel):
    title = models.CharField(max_length=255, null=True, blank=True)

    # Поля для чатов по определенным темам - вакансии/магазины и т.д.
    subject_user = models.ForeignKey(
        UserProfile, null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Основной участник чата'
    )
    target_id = models.PositiveIntegerField(null=True, blank=True)
    target_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='chat_target_ct',
        verbose_name='Объект обсуждения в чате'
    )
    target_ct_name = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='Имя модели - объекта обсуждения в чате'
    )
    target = GenericForeignKey(ct_field='target_ct', fk_field='target_id')
    # ####

    users = models.ManyToManyField(
        UserProfile, through='ChatUser', blank=True, related_name='chats', verbose_name='Участники чата'
    )

    state = models.PositiveIntegerField(
        choices=choices(ChatManagerState), default=ChatManagerState.BOT_IS_USED.value,
        verbose_name='Участие менеджера в чате'
    )

    active_managers = models.ManyToManyField(
        UserProfile, db_table='app_chats__active_managers',
        verbose_name='Активные менеджеры', related_name='ruled_chats'
    )

    def __str__(self):
        return f'{self.id} - {self.subject_user.username if self.subject_user else None}=>{self.target_ct_name}'

    class Meta:
        db_table = 'app_chats'
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'


class ChatUser(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    is_bot_enabled = models.BooleanField(default=True, verbose_name='Бот для чата включен')
    bot_state = models.IntegerField(
        default=ChatterBotStates.IDLE.value, choices=choices(ChatterBotStates), verbose_name='Состояние бота для СМЗ'
    )
    blocked_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата блокировки')

    def __str__(self):
        return f'CHAT ID{self.chat_id}=>USER ID{self.user_id}'

    class Meta:
        db_table = 'app_chats__chat_user'
        verbose_name = 'Участник чата'
        verbose_name_plural = 'Участники чатов'


class Message(BaseModel):
    user = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='messages')
    chat = models.ForeignKey(Chat, null=True, blank=True, on_delete=models.SET_NULL, related_name='messages')

    title = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField(null=True, blank=True)

    message_type = models.PositiveIntegerField(choices=choices(ChatMessageType), default=ChatMessageType.SIMPLE.value)
    attachments = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    read_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата прочтения собеседником моего сообщения')
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    icon_type = models.PositiveIntegerField(choices=choices(ChatMessageIconType), null=True, blank=True)
    buttons = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f'{self.id} - {self.user.username}'

    class Meta:
        db_table = 'app_chats__messages'
        verbose_name = 'Сообщение в чате'
        verbose_name_plural = 'Сообщения в чатах'


class MessageStat(BaseModel):
    user = models.ForeignKey(UserProfile, null=True, blank=True, on_delete=models.SET_NULL,
                             related_name='interacted_messages')
    message = models.ForeignKey(Message, null=True, blank=True, on_delete=models.SET_NULL, related_name='stats')
    chat = models.ForeignKey(Chat, null=True, blank=True, on_delete=models.SET_NULL, related_name='messages_stats')

    is_read = models.BooleanField(default=False, verbose_name='Прочитано')

    def __str__(self):
        return f'{self.message.text} - {self.user.username}'

    class Meta:
        db_table = 'app_chats__message_stat'
        verbose_name = 'Состояние сообщения для пользователя'
        verbose_name_plural = 'Состояния сообщений для пользователей'
