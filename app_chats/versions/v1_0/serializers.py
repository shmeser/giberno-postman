from rest_framework import serializers

from app_chats.models import Chat, Message
from app_media.enums import MediaType
from app_media.versions.v1_0.controllers import MediaController
from app_users.models import UserProfile
from backend.fields import DateTimeField


class ChatsSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()

    last_message = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()

    def get_users(self, data):
        return ChatProfileSerializer(data.users, many=True).data

    def get_last_message(self, data):
        return LastMessagesSerializer(data.last_message[0], many=False).data

    class Meta:
        model = Chat
        fields = [
            'id',
            'title',
            'created_at',
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
            'id',
            'user_id',
            'title',
            'text',
            'message_type',
            'form_status',
            'created_at',
            'read_at',
        ]


class MessageProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    def get_avatar(self, prefetched_data):
        return MediaController(self.instance).get_related_images_urls(prefetched_data, MediaType.AVATAR.value)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "avatar"
        ]


class ChatProfileSerializer(MessageProfileSerializer):
    online = serializers.SerializerMethodField()

    def get_online(self, data):
        return data.sockets.count() > 0

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "username",
            "first_name",
            "middle_name",
            "last_name",
            "online",
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
            'id',
            'user_id',
            'title',
            'text',
            'message_type',
            'form_status',
            'created_at',
            'read_at',
            'attachments',
        ]
