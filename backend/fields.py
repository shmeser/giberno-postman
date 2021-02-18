from rest_framework import serializers

from app_media.enums import MediaFormat
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer
from backend.utils import datetime_to_timestamp, timestamp_to_datetime


class DateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        return datetime_to_timestamp(value)

    def to_internal_value(self, value):
        return timestamp_to_datetime(int(value))


class ImageField(serializers.SerializerMethodField):
    def __init__(self, field_name, media_type, check_platform=False, **kwargs):
        """
        :param field_name: Название поля, которое выдаст сериалайзер
        :param media_type: тип изображения из енума MediaType
        :param check_platform: Проверять платформу. Если True - для iOS mime_type='image/png', Android='image/svg+xml'
        :param kwargs:
        """
        kwargs['method_name'] = f'get_{field_name}'
        super().__init__(**kwargs)
        self.media_type = media_type
        self.check_platform = check_platform

    def to_representation(self, prefetched_data):
        file = MediaRepository.get_related_media_file(
            self.parent.instance, prefetched_data, self.media_type, MediaFormat.IMAGE.value,
            # Берем из родительского сериалайзера, в котором init определяет mime_type, если нет - None
            self.parent.mime_type if hasattr(self.parent, 'mime_type') and self.check_platform else None
        )

        if file:
            return MediaSerializer(file, many=False).data
        return None


class FlexibleIOField(serializers.IntegerField):
    """
    поле предназначено для создание записи по ID, и отдачи записи в
    сериализованном виде.
    """

    def __init__(self, serializer, repository=None, is_m2m=False, **kwargs):
        self.is_m2m = is_m2m
        self.serializer = serializer
        self.repository = repository
        super().__init__(**kwargs)

    def to_representation(self, value):
        return self.serializer(value, many=self.is_m2m).data

    def to_internal_value(self, value):
        if self.serializer.repository and type(value) == int:
            return self.serializer.repository().get_by_id(value)
        elif self.serializer.repository and self.is_m2m and type(value) == list:
            return [self.serializer.repository().get_by_id(i) for i in value]
        return value
