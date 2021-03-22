from django.contrib.contenttypes.models import ContentType
from loguru import logger

from app_chats.models import Chat, Message, ChatUser
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

        # TODO без указания target, создаем чат p2p

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

    @staticmethod
    def create_chat(users, title=None, target_id=None, target_model=None, subject_user=None):
        ct = ContentType.objects.get_for_model(target_model) if target_model else None
        chat = Chat.objects.create(
            title=title,
            subject_user=subject_user,
            target_id=target_id,
            target_ct=ct,
            target_ct_name=ct.modelt if ct else None
        )

        chat_users = [ChatUser(chat=chat, user=u) for u in users]
        ChatUser.objects.bulk_create(chat_users)

    def should_create_chat(self, kwargs):
        if self.me:  # Если роль менеджера
            pass

        if self.me:  # Если роль пользователя
            pass

        return True

    def get_chats_or_create(self, kwargs, paginator=None, order_by: list = None):
        should_create_chat = self.should_create_chat(kwargs)

        self.modify_kwargs(kwargs, order_by)  # Изменяем kwargs для работы с objects.filter(**kwargs)

        records = self.base_query.exclude(deleted=True).filter(**kwargs)

        if not records:
            # Если не найдены нужные чаты
            if should_create_chat:
                self.create_chat(
                    users=[
                        self.me
                    ]
                )
            return self.base_query.filter(**kwargs)
        if order_by:
            records = records.order_by(*order_by)

        return records[paginator.offset:paginator.limit] if paginator else records

        # return self.fast_related_loading(  # Предзагрузка связанных сущностей
        #     queryset=records[paginator.offset:paginator.limit] if paginator else records,
        # )


class MessagesRepository(MasterRepository):
    model = Message
