from backend.errors.enums import RESTErrors
from backend.errors.http_exceptions import HttpException
from backend.models import BaseModel


class BaseRepository:
    model = None

    def __init__(self, model_class) -> None:
        super().__init__()
        self.model: BaseModel = model_class

    def get_all(self, paginator=None, order_by: list = None):
        if order_by:
            records = self.model.objects.order_by(*order_by).filter(deleted=False).all()
        else:
            records = self.model.objects.filter(deleted=False).all()
        return records[paginator.offset:paginator.limit] if paginator else records[:1000]

    def get_by_id(self, record_id):
        try:
            return self.model.objects.get(id=record_id)
        except self.model.DoesNotExist:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден'
            )

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.model.objects.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
            else:
                records = self.model.objects.exclude(deleted=True).filter(**kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.model.objects.order_by(*order_by).filter(**kwargs)
            else:
                records = self.model.objects.filter(**kwargs)
        return records[paginator.offset:paginator.limit] if paginator else records  # [:100]

    def filter(self, args: list = None, kwargs={}, paginator=None, order_by: list = None):
        try:
            if order_by:
                records = self.model.objects.order_by(*order_by).exclude(deleted=True).filter(args, **kwargs)
            else:
                records = self.model.objects.exclude(deleted=True).filter(args, **kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.model.objects.order_by(*order_by).filter(args, **kwargs)
            else:
                records = self.model.objects.filter(args, **kwargs)
        return records[paginator.offset:paginator.limit] if paginator else records  # [:100]

    def create(self, **kwargs):
        return self.model.objects.create(**kwargs)

    def update(self, record_id, **kwargs):
        if self.model.objects.filter(id=record_id).exists():
            self.model.objects.filter(id=record_id).update(**kwargs)
            return self.get_by_id(record_id)
        else:
            raise HttpException(status_code=RESTErrors.NOT_FOUND.value,
                                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')

    def update_or_create(self, record_id, **kwargs):
        if record_id:
            return self.update(record_id, **kwargs)
        else:
            return self.create(**kwargs)

    def delete(self, record_id):
        record = self.get_by_id(record_id)
        record.deleted = True
        record.save()
        return record

    def hard_delete(self, record_id):
        return self.get_by_id(record_id).delete()

    def delete_by_kwargs(self, kwargs):
        return self.model.objects.filter(**kwargs).update({'deleted': True})

    def hard_delete_by_kwargs(self, kwargs):
        return self.model.objects.filter(**kwargs).delete()
