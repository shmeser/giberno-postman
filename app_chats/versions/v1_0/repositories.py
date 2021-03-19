from django.contrib.contenttypes.models import ContentType
from loguru import logger

from app_chats.models import Chat, Message
from app_market.models import Shop, Vacancy
from backend.mixins import MasterRepository
from backend.utils import timestamp_to_datetime


class ChatsRepository(MasterRepository):
    model = Chat

    def __init__(self, me=None) -> None:
        super().__init__()

        self.me = me  # TODO проверить роль

        # В зависимости от роли фильтровать списки чатов

        # Чат создается в следующих случаях:
        # - Пользователь запросил чат по вакансии/магазину, если такого еще нет
        # - Менеджер запросил чат с пользователем по откликнувшейся им вакансии, если такого еще нет

        # Обычный пользователь может создать чат по любой вакансии и по любому магазину
        # Менеджер - только по тем вакансиям, которые ему доступны

        # Чат не создается менеджером, если не переданы оба параметра (пользователь и вакансия),
        # на вакансию пользователь должен откликнуться заранее

        # Выражения для вычисляемых полей в annotate
        # self.distance_expression = Distance('shop__location', point) if point else Value(None, IntegerField())
        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects  ##.annotate(
        # distance=self.distance_expression,
        # )

    def modify_kwargs(self, kwargs, order_by):
        shop_id = kwargs.pop('shop_id', None)
        if shop_id:
            kwargs.update({
                'target_ct_id': ContentType.objects.get_for_model(Shop).id,
                'target_id': shop_id
            })

        vacancy_id = kwargs.pop('vacancy_id', None)
        if vacancy_id:
            kwargs.update({
                'target_ct_id': ContentType.objects.get_for_model(Vacancy).id,
                'target_id': vacancy_id
            })

        created_at = kwargs.pop('created_at', None)
        if created_at:
            try:
                created_at = timestamp_to_datetime(int(created_at))
                if '-created_at' in order_by:
                    kwargs.update({
                        'created_at__lte': created_at
                    })
                if 'created_at' in order_by:
                    kwargs.update({
                        'created_at__gte': created_at
                    })

            except Exception as e:
                logger.error(e)

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        self.modify_kwargs(kwargs, order_by)  # Изменяем kwargs для работы с objects.filter(**kwargs)
        try:
            if order_by:
                records = self.base_query.order_by(*order_by).exclude(deleted=True).filter(**kwargs)
            else:
                records = self.base_query.exclude(deleted=True).filter(**kwargs)
        except Exception:  # no 'deleted' field
            if order_by:
                records = self.base_query.order_by(*order_by).filter(**kwargs)
            else:
                records = self.base_query.filter(**kwargs)

        return records[paginator.offset:paginator.limit] if paginator else records

        # return self.fast_related_loading(  # Предзагрузка связанных сущностей
        #     queryset=records[paginator.offset:paginator.limit] if paginator else records,
        # )


class MessagesRepository(MasterRepository):
    model = Message
