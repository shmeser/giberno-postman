from django.contrib.contenttypes.models import ContentType

from app_chats.models import Chat, Message
from app_market.models import Shop, Vacancy
from backend.mixins import MasterRepository


class ChatsRepository(MasterRepository):
    model = Chat

    def __init__(self, me=None) -> None:
        super().__init__()

        self.me = me

        # Выражения для вычисляемых полей в annotate
        # self.distance_expression = Distance('shop__location', point) if point else Value(None, IntegerField())
        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects ##.annotate(
            # distance=self.distance_expression,
        # )

    def modify_kwargs(self, kwargs):
        shop_id = kwargs.pop('shop', None)
        if shop_id:
            kwargs.update({
                'target_ct_id': ContentType.objects.get_for_model(Shop).id,
                'target_id': shop_id
            })

        vacancy_id = kwargs.pop('vacancy', None)
        if vacancy_id:
            kwargs.update({
                'target_ct_id': ContentType.objects.get_for_model(Vacancy).id,
                'target_id': vacancy_id
            })

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        self.modify_kwargs(kwargs)  # Изменяем kwargs для работы с objects.filter(**kwargs)
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
