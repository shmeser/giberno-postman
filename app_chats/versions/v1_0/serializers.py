from rest_framework import serializers

from app_chats.models import Chat, Message
from app_media.enums import MediaType
from app_media.versions.v1_0.controllers import MediaController
from app_users.models import UserProfile
from backend.fields import DateTimeField
from backend.mixins import CRUDSerializer
from backend.utils import chained_get


class ChatsSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.me = chained_get(kwargs, 'context', 'me')
        self.unread_count = chained_get(kwargs, 'context', 'unread_count')

    created_at = DateTimeField()

    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    vacancy = serializers.SerializerMethodField()
    shop = serializers.SerializerMethodField()
    subject_user = serializers.SerializerMethodField()

    def get_vacancy(self, data):
        if data.target and data.target._meta.model_name == 'vacancy':
            return {
                'id': data.target.id,
                'title': data.target.title,
                'price': data.target.price
            }

    def get_shop(self, data):
        if data.target and data.target._meta.model_name == 'shop':
            return {
                'id': data.target.id,
                'title': data.target.title,
            }

    def get_subject_user(self, data):
        return ChatSubjectUserSerializer(data.subject_user, many=False, context={'me': self.me}).data

    def get_users(self, data):
        return ChatProfileSerializer(data.users, many=True, context={'me': self.me}).data

    def get_last_message(self, data):
        if data.prefetched_messages:
            return LastMessagesSerializer(data.prefetched_messages[0], many=False).data
        else:
            return None

    def get_unread_count(self, data):
        if self.unread_count:  # Данные из context, используется в сокетах для отправки нужных данных участникам чата
            return self.unread_count
        if getattr(data, 'unread_count', None):
            return data.unread_count
        return 0

    class Meta:
        model = Chat
        fields = [
            'id',
            'title',
            'created_at',
            'unread_count',
            'last_message',
            'users',
            'vacancy',
            'shop',
            'subject_user',
        ]


class ChatSerializer(ChatsSerializer):
    class Meta:
        model = Chat
        fields = [
            'id',
            'title',
            'created_at',
            'unread_count',
            'last_message',
            'users',
            'vacancy',
            'shop',
            'subject_user',
        ]


class LastMessagesSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()
    read_at = DateTimeField()

    class Meta:
        model = Message
        fields = [
            'uuid',
            'user_id',
            'title',
            'text',
            'message_type',
            'form_status',
            'created_at',
            'read_at',
        ]


class ChatProfileSerializer(CRUDSerializer):
    avatar = serializers.SerializerMethodField()
    online = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()

    def get_avatar(self, prefetched_data):
        return MediaController(self.instance).get_related_images_urls(prefetched_data, MediaType.AVATAR.value)

    def get_online(self, data):
        return data.sockets.count() > 0

    def get_is_me(self, data):
        return self.me == data

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "online",
            "is_me",
            "avatar"
        ]


class ChatSubjectUserSerializer(CRUDSerializer):
    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
        ]


class MessagesSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()
    read_at = DateTimeField()
    attachments = serializers.SerializerMethodField()

    def get_attachments(self, prefetched_data):
        return MediaController(self.instance).get_related_media_urls(
            prefetched_data,
            MediaType.ATTACHMENT.value,
            multiple=True
        )

    class Meta:
        model = Message
        fields = [
            'id',
            'uuid',
            'user_id',
            'chat_id',
            'title',
            'text',
            'message_type',
            'form_status',
            'created_at',
            'read_at',
            'attachments',
        ]
