from rest_framework import serializers

from app_chats.models import Chat, Message
from app_media.enums import MediaType
from app_media.versions.v1_0.controllers import MediaController
from app_users.models import UserProfile
from backend.fields import DateTimeField
from backend.mixins import CRUDSerializer


class ChatsSerializer(CRUDSerializer):
    created_at = DateTimeField()

    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()

    def get_users(self, data):
        return ChatProfileSerializer(data.users, many=True, context={'me': self.me}).data

    def get_last_message(self, data):
        if data.last_message:
            return LastMessagesSerializer(data.last_message[0], many=False).data
        else:
            return None

    def get_unread_count(self, data):
        return 0

    class Meta:
        model = Chat
        fields = [
            'id',
            'title',
            'created_at',
            'unread_count',
            'last_message',
            'users'
        ]


class ChatSerializer(ChatsSerializer):
    class Meta:
        model = Chat
        fields = [
            'id',
            'title',
            'created_at',
            'last_message',
            'users'
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
            'uuid',
            'user_id',
            'title',
            'text',
            'message_type',
            'form_status',
            'created_at',
            'read_at',
            'attachments',
        ]
