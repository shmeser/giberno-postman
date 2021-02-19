from app_media.enums import MediaFormat
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer


class MediaController:
    def __init__(self, model_instance, mime_type=None):
        """
        :param model_instance: Модель, для которой будет найден медиафайл
        :param mime_type:  Передавать, если нужны разные форматы изображений для каждой из платформ (iOS, Android)
        """
        self.instance = model_instance
        self.mime_type = mime_type

    def get_related_image(self, prefetched_data, media_type):
        file = MediaRepository.get_related_media_file(
            self.instance, prefetched_data, media_type, MediaFormat.IMAGE.value, mime_type=self.mime_type
        )
        return MediaSerializer(file, many=False).data if file else None
