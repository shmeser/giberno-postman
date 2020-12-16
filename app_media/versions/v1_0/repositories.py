from app_media.models import MediaModel
from backend.entity import File
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository


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

        self.model.objects.bulk_create(media_models)
