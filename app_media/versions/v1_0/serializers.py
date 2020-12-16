from rest_framework import serializers

from app_media.models import MediaModel


class MediaSerializer(serializers.Serializer):
    class Meta:
        model = MediaModel
        fields = [
            '__all__'
        ]
