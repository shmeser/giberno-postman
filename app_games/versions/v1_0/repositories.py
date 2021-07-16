from app_games.models import Prize, Task
from app_media.enums import MediaType
from app_media.models import MediaModel
from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.mixins import MasterRepository


class PrizesRepository(MasterRepository):
    model = Prize

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def set_like(self, record_id):
        prize = self.get_by_id(record_id)
        # TODO проверка на уровень приза, если лайкается с тем же уровнем либо все уровни пролайканы, то ошибка

    def remove_like(self, record_id):
        prize = self.get_by_id(record_id)

    @staticmethod
    def get_conditions_for_promotion():
        promo_documents = MediaModel.objects.filter(
            owner_id=None, type=MediaType.PROMO_TERMS.value, deleted=False
        )

        return promo_documents

    def get_cards(self):
        return self.model.objects.filter(deleted=False)


class TasksRepository(MasterRepository):
    model = Task

    def __init__(self, me=None) -> None:
        super().__init__()
        self.me = me

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def get_tasks(self, filters, order, paginator):
        return []
