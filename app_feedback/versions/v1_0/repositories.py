from app_feedback.models import Comment
from backend.errors.enums import RESTErrors
from backend.errors.http_exception import HttpException
from backend.mixins import MasterRepository


class CommentsRepository(MasterRepository):
    model = Comment

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id, is_staff=False)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )
