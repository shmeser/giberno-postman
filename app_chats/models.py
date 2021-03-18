import uuid as uuid

from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from app_chats.enums import ChatMessageType, FormMessageStatus
from app_media.models import MediaModel
from app_users.models import UserProfile
from backend.models import GenericSourceTargetBase, BaseModel
from backend.utils import choices


class Chat(GenericSourceTargetBase):
    title = models.CharField(max_length=255, null=True, blank=True)

    owner_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='chat_owner_ct',
        verbose_name='Основной участник чата'
    )
    target_ct = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='chat_target_ct',
        verbose_name='Объект обсуждения в чате'
    )

    users = models.ManyToManyField(UserProfile, through='ChatUser', blank=True, related_name='chats')

    def __str__(self):
        return f'{self.id} - {self.owner_ct_name}=>{self.target_ct_name}'

    class Meta:
        db_table = 'app_chats'
        verbose_name = 'Чат'
        verbose_name_plural = 'Чаты'


class ChatUser(BaseModel):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    blocked_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата блокировки')

    def __str__(self):
        return f'CHAT ID{self.chat_id}=>USER ID{self.user_id}'

    class Meta:
        db_table = 'app_chats__chat_user'
        verbose_name = 'Участник чата'
        verbose_name_plural = 'Участники чатов'


class Message(BaseModel):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, null=True, blank=True, on_delete=models.SET_NULL)

    text = models.TextField(null=True, blank=True)

    message_type = models.PositiveIntegerField(choices=choices(ChatMessageType), default=ChatMessageType.SIMPLE.value)
    attachments = GenericRelation(MediaModel, object_id_field='owner_id', content_type_field='owner_ct')

    # Generic Relation - если нет владельца, значит писал бот
    owner_id = models.PositiveIntegerField(null=True, blank=True)
    owner_ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL, related_name='owner_ct')
    owner_ct_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя модели - владельца')
    owner = GenericForeignKey(ct_field='owner_ct', fk_field='owner_id')

    form_status = models.PositiveIntegerField(
        choices=choices(FormMessageStatus),
        default=FormMessageStatus.INITIAL.value,
        verbose_name='Статус обработки сообщения с типом ФОРМА'
    )
    read_at = models.DateTimeField(blank=True, null=True, verbose_name='Дата прочтения собеседником')

    def __str__(self):
        return f'{self.id} - {self.owner_ct_name}'

    class Meta:
        db_table = 'app_chats__messages'
        verbose_name = 'Сообщение в чате'
        verbose_name_plural = 'Сообщения в чатах'
