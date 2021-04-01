from rest_framework import serializers

from app_media.models import MediaModel


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaModel
        fields = [
            'uuid',
            'title',
            'file',
            'preview',
            'format',
            'type',
            'mime_type'
        ]


class MediaUrlsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaModel
        fields = [
            'file',
            'preview',
        ]
