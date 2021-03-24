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

    def get_related_images(self, prefetched_data, media_type, multiple=False):
        empty = [] if multiple else None
        files = MediaRepository.get_related_media(
            self.instance, prefetched_data, media_type, MediaFormat.IMAGE.value, mime_type=self.mime_type,
            multiple=multiple
        )
        return MediaSerializer(files, many=multiple).data if files else empty

    def get_related_images_preview(self, prefetched_data, media_type, multiple=False):
        """ Облегченная версия изображения, только ссылка на превью """
        empty = [] if multiple else None
        file = MediaRepository.get_related_media(
            self.instance, prefetched_data, media_type, MediaFormat.IMAGE.value, mime_type=self.mime_type,
            multiple=multiple
        )
        return MediaPreviewSerializer(file, many=multiple).data if file else empty

    def get_related_media(self, prefetched_data, media_type, multiple=False):
        empty = [] if multiple else None
        file = MediaRepository.get_related_media(self.instance, prefetched_data, media_type, multiple=multiple)
        return MediaSerializer(file, many=multiple).data if file else empty

    def get_related_media_file(self, prefetched_data, media_type, multiple=False):
        """ Облегченная версия файла только ссылка на файл """
        empty = [] if multiple else None
        file = MediaRepository.get_related_media(self.instance, prefetched_data, media_type, multiple=multiple)
        return MediaFileSerializer(file, many=multiple).data if file else empty
