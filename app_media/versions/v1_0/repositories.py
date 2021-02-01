from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from app_media.models import MediaModel
from backend.entity import File
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository
from backend.utils import chained_get


class MediaRepository(MasterRepository):
    model = MediaModel

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, is_staff=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail='Объект %s с ID=%d не найден' % (self.model._meta.verbose_name, record_id)
            )

    def bulk_create(self, files: [File]):
        media_models = []
        for file in files:
            media_models.append(
                self.model(**dict(file))
            )

        return self.model.objects.bulk_create(media_models)

    @staticmethod
    def get_related_media_file(model_instance, data, media_type, media_format):
        medias_list = chained_get(data, 'medias', default=list())
        if isinstance(model_instance, QuerySet):
            # для many=True
            file = None
            # Берем флаг из предзагруженного поля medias
            if medias_list:
                file = next(filter(lambda x: x.type == media_type, chained_get(data, 'medias')), None)
        else:
            if medias_list:
                file = next(filter(lambda x: x.type == media_type, chained_get(data, 'medias')), None)
            else:
                file = MediaModel.objects.filter(
                    owner_id=data.id, type=media_type,
                    owner_ct_id=ContentType.objects.get_for_model(data).id, format=media_format,
                ).order_by('-created_at').first()

        return file
