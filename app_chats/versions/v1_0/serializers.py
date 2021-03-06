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

    created_at = DateTimeField()
    blocked_at = DateTimeField()
    active_managers_ids = serializers.SerializerMethodField()

    first_unread_message = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    vacancy = serializers.SerializerMethodField()
    shop = serializers.SerializerMethodField()
    distributor_logo = serializers.SerializerMethodField()
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
                'address': data.target.address,
            }

    def get_subject_user(self, data):
        if not data.subject_user:
            return None
        return ChatSubjectUserSerializer(data.subject_user, many=False, context={'me': self.me}).data

    def get_users(self, data):
        return ChatProfileSerializer(data.users, many=True, context={'me': self.me}).data

    def get_last_message(self, data):
        if data.last_messages:
            return LastMessagesSerializer(data.last_messages[0], many=False).data
        else:
            return None

    def get_first_unread_message(self, data):
        if getattr(data, 'first_unread_messages', None):
            return FirstUnreadMessageSerializer(data.first_unread_messages[0], many=False).data
        else:
            return None

    def get_unread_count(self, data):
        if getattr(data, 'unread_count', None):
            return data.unread_count
        return 0

    def get_active_managers_ids(self, data):
        if getattr(data, 'active_managers_ids', None):
            return data.active_managers_ids
        return []

    def get_distributor_logo(self, data):
        # ???????????? ???? prefetch_related
        if data.target and data.target._meta.model_name == 'vacancy':
            return MediaController(data.target).get_related_images_urls(
                data.target.shop.distributor, MediaType.LOGO.value, only_prefetched=True
            )
        if data.target and data.target._meta.model_name == 'shop':
            return MediaController(data.target).get_related_images_urls(
                data.target.distributor, MediaType.LOGO.value, only_prefetched=True
            )
        return None

    class Meta:
        model = Chat
        fields = [
            'id',
            'title',
            'created_at',
            'blocked_at',
            'unread_count',
            'state',
            'distributor_logo',
            'active_managers_ids',
            'first_unread_message',
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
            'blocked_at',
            'unread_count',
            'state',
            'distributor_logo',
            'active_managers_ids',
            'first_unread_message',
            'last_message',
            'users',
            'vacancy',
            'shop',
            'subject_user',
        ]


class SocketChatSerializer(ChatsSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unread_count = chained_get(kwargs, 'context', 'unread_count')
        self.first_unread_message = chained_get(kwargs, 'context', 'first_unread_message')

    def get_first_unread_message(self, data):
        # ???????????? ???? context, ???????????????????????? ?? ?????????????? ?????? ???????????????? ???????????? ???????????? ???????????????????? ????????
        if self.first_unread_message:
            return self.first_unread_message
        return None

    def get_unread_count(self, data):
        # ???????????? ???? context, ???????????????????????? ?? ?????????????? ?????? ???????????????? ???????????? ???????????? ???????????????????? ????????
        if self.unread_count:
            return self.unread_count
        return 0

    class Meta:
        model = Chat
        fields = [
            'id',
            'unread_count',
            'state',
            'blocked_at',
            'first_unread_message',
            'last_message',
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
            'icon_type',
            'created_at',
            'read_at',
        ]


class FirstUnreadMessageSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()

    class Meta:
        model = Message
        fields = [
            'uuid',
            'created_at',
        ]


class ChatProfileSerializer(CRUDSerializer):
    avatar = serializers.SerializerMethodField()
    online = serializers.SerializerMethodField()
    is_me = serializers.SerializerMethodField()

    def get_avatar(self, prefetched_data):
        return MediaController(self.instance).get_related_images_urls(
            prefetched_data, MediaType.AVATAR.value, only_prefetched=True
        )

    def get_online(self, data):
        return data.sockets.count() > 0

    def get_is_me(self, data):
        return self.me == data

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "account_type",
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
            multiple=True,
            only_prefetched=True
        )

    class Meta:
        model = Message
        fields = [
            'uuid',
            'user_id',
            'chat_id',
            'title',
            'text',
            'message_type',
            'icon_type',
            'created_at',
            'read_at',
            'attachments',
            'buttons'
        ]
