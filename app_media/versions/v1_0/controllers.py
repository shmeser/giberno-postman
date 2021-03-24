from app_media.enums import MediaFormat
from app_media.versions.v1_0.repositories import MediaRepository
from app_media.versions.v1_0.serializers import MediaSerializer, MediaPreviewSerializer, MediaFileSerializer


class MediaController:
    def __init__(self, model_instance, mime_type=None):
        """
        :param model_instance: Модель, для которой будет найден медиафайл
        :param mime_type:  Передавать, если нужны разные форматы изображений для каждой из платформ (iOS, Android)
        """
        self.instance = model_instance
        self.mime_type = mime_type

    def get_related_images(self, prefetched_data, media_type):
        file = MediaRepository.get_related_media(
            self.instance, prefetched_data, media_type, MediaFormat.IMAGE.value, mime_type=self.mime_type
        )
        return MediaSerializer(file, many=False).data if file else None

    def get_related_images_preview(self, prefetched_data, media_type):
        """ Облегченная версия изображения, только ссылка на превью """
        file = MediaRepository.get_related_media(
            self.instance, prefetched_data, media_type, MediaFormat.IMAGE.value, mime_type=self.mime_type
        )
        return MediaPreviewSerializer(file, many=False).data if file else None

    def get_related_media(self, prefetched_data, media_type):
        file = MediaRepository.get_related_media(self.instance, prefetched_data, media_type)
        return MediaSerializer(file, many=False).data if file else None

    def get_related_media_file(self, prefetched_data, media_type):
        """ Облегченная версия файла только ссылка на файл """
        file = MediaRepository.get_related_media(self.instance, prefetched_data, media_type)
        return MediaFileSerializer(file, many=False).data if file else None
