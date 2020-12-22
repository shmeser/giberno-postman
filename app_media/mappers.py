import uuid as uuid

from django.contrib.contenttypes.models import ContentType

from app_media.enums import MediaType, MediaFormat
from backend.entity import File, Error
from backend.errors.enums import ErrorsCodes
from backend.errors.http_exception import CustomException
from backend.utils import get_media_format, resize_image, convert_video


class MediaMapper:
    @staticmethod
    def combine(file_data, owner, file_title=None, file_type=MediaType.OTHER):

        file_entity = File()
        file_entity.uuid = uuid.uuid4()

        file_entity.title = file_title
        file_entity.type = file_type

        owner_content_type = ContentType.objects.get_for_model(owner)
        file_entity.owner_content_type_id = owner_content_type.id
        file_entity.owner_content_type = owner_content_type.model
        file_entity.owner_id = owner.id

        file_entity.mime_type = file_data.content_type
        file_entity.format = get_media_format(file_entity.mime_type)
        file_entity.size = file_data.size

        name = str(file_entity.uuid)
        parts = file_data.name.split('.')
        if parts.__len__() > 1:
            extension = '.' + parts[-1].lower()
        else:
            extension = ''
        file_data.name = name + extension

        file_entity.file = file_data
        file_entity.mime_type = file_data.content_type

        if file_entity.format == MediaFormat.IMAGE:
            resize_image(file_entity)
        if file_entity.format == MediaFormat.AUDIO:
            # duration
            pass
        if file_entity.format == MediaFormat.VIDEO:
            # width
            # height
            # duration
            # preview
            convert_video(file_entity)
        if file_entity.format == MediaFormat.UNKNOWN:  # Если пришел неизвестный формат файла
            raise CustomException(errors=[
                dict(Error(ErrorsCodes.UNSUPPORTED_FILE_FORMAT))
            ])

        # Не создаем пустые записи, если файл не удалось обработать
        if file_entity.file is not None:
            return file_entity

        return None
