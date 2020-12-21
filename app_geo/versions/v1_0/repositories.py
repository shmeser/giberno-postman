from app_geo.models import Language
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository


class LanguagesRepository(MasterRepository):
    model = Language

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, is_staff=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail='Объект %s с ID=%d не найден' % (self.model._meta.verbose_name, record_id)
            )
