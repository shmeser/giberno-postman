from rest_framework import serializers

from backend.utils import datetime_to_timestamp, timestamp_to_datetime


# from media.repositories import MediaRepository
# from media.serializers import MediaSerializer


class DateTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        return datetime_to_timestamp(value)

    def to_internal_value(self, value):
        return timestamp_to_datetime(int(value))


# class MediaField(serializers.IntegerField):
#     def __init__(self, is_m2m=False, max_files_count=5, **kwargs):
#         self.is_m2m = is_m2m
#         if self.is_m2m:
#             self.validators.append(ValidateFilesCount(max_files_count))
#         super().__init__(**kwargs)
#
#     def to_representation(self, value):
#         return MediaSerializer(value, many=self.is_m2m).data
#
#     def to_internal_value(self, value):
#         # если m2m, то, передан список, и, можно сделать фильтр по нему
#         if self.is_m2m:
#             return MediaRepository().get_all(paginator=None).filter(id__in=value)
#         return MediaRepository().get_medias().get(id=value)


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
