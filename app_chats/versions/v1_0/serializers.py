from rest_framework import serializers

from app_chats.models import Chat, Message
from backend.fields import DateTimeField


class ChatsSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()

    last_message = serializers.SerializerMethodField()

    def get_last_mesasge(self, data):
        return None

    class Meta:
        model = Chat
        fields = [
            'id',
            'title',
            'text',
            'created_at',
            'last_message'
        ]


class ChatSerializer(ChatsSerializer):
    class Meta:
        model = Chat
        fields = [
            'id',
            'title',
            'text',
            'created_at',
            'last_message'
        ]


class MessagesSerializer(serializers.ModelSerializer):
    created_at = DateTimeField()

    class Meta:
        model = Message
        fields = [
            'id',
            'text',
            'created_at'
        ]
