from django.contrib.contenttypes.models import ContentType
from loguru import logger

from app_chats.models import Chat, Message, ChatUser
from app_market.models import Shop, Vacancy
from app_users.versions.v1_0.repositories import ProfileRepository
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
        user_id = kwargs.pop('user_id', None)
        shop_id = kwargs.pop('shop_id', None)
        vacancy_id = kwargs.pop('vacancy_id', None)
        created_at = kwargs.pop('created_at', None)

        checking_kwargs = {}

        # Данные для создаваемого чата
        users = []
        title = None
        target_id = None
        target_ct = None
        subject_user = None

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

        if self.me is None:  # Если роль менеджера
            if user_id and vacancy_id:
                # Цель обсуждения в чате - вакансия
                target_ct = ContentType.objects.get_for_model(Vacancy)
                target_id = vacancy_id
                # Основной пользователь в чате - самозанятый
                subject_user = ProfileRepository().get_by_id(user_id)
                # Участники чата
                users = [
                    self.me,
                    subject_user
                ]

        elif self.me:  # Если роль пользователя
            if user_id:  # user-user
                # Цели обсуждения в чате нет по умолчанию для такого чата

                # Участники чата
                # TODO чат с самим собой?
                users = [
                    self.me,
                    ProfileRepository().get_by_id(user_id)
                ]
                kwargs.update({
                    'users__in': users,
                })
                checking_kwargs.update({
                    'users__in': users,
                })

            elif shop_id:  # user-shop
                # Цель обсуждения в чате - магазин
                target_ct = ContentType.objects.get_for_model(Shop)
                target_id = shop_id
                # Основной пользователь в чате - самозанятый
                subject_user = self.me
                # Участники чата
                users = [
                    subject_user,
                    # TODO менеджер добавляется в чат на других этапах, при создании чата неизвестно кто присоединится
                ]
            elif vacancy_id:  # user-vacancy
                # Цель обсуждения в чате - вакансия
                target_ct = ContentType.objects.get_for_model(Vacancy)
                target_id = vacancy_id
                # Основной пользователь в чате - самозанятый
                subject_user = self.me
                # Участники чата
                users = [
                    subject_user,
                    # TODO менеджер, создавший вакансию
                ]

        target_ct_id = target_ct.id if target_ct else None
        target_ct_name = target_ct.model if target_ct else None

        updater = {
            'subject_user': subject_user,
            'target_ct_id': target_ct_id,
            'target_id': target_id
        }

        kwargs.update(updater)
        checking_kwargs.update(updater)

        chat_data = {
            'users': users,
            'title': title,
            'target_id': target_id,
            'target_ct_id': target_ct_id,
            'target_ct_name': target_ct_name,
            'subject_user': subject_user,
        }

        return checking_kwargs, chat_data

    @staticmethod
    def create_chat(users, title=None, target_id=None, target_ct_id=None, target_ct_name=None, subject_user=None):
        chats = Chat.objects.filter(
            title=title,
            subject_user=subject_user,
            target_id=target_id,
            target_ct_id=target_ct_id,
            target_ct_name=target_ct_name,
            users__in=users
        )

        if not chats:
            chat = Chat.objects.create(
                title=title,
                subject_user=subject_user,
                target_id=target_id,
                target_ct_id=target_ct_id,
                target_ct_name=target_ct_name
            )
            chat_users = [ChatUser(chat=chat, user=u) for u in users]
            ChatUser.objects.bulk_create(chat_users)

    def get_chats_or_create(self, kwargs, paginator=None, order_by: list = None):
        # Изменяем kwargs для работы с objects.filter(**kwargs)
        checking_kwargs, chat_data = self.modify_kwargs(kwargs, order_by)

        if not self.base_query.filter(**checking_kwargs).exists() and chat_data:
            # Если не найдены нужные чаты
            self.create_chat(
                users=chat_data['users'],
                title=chat_data['title'],
                target_id=chat_data['target_id'],
                target_ct_id=chat_data['target_ct_id'],
                target_ct_name=chat_data['target_ct_name'],
                subject_user=chat_data['subject_user']
            )

        records = self.base_query.exclude(deleted=True).filter(**kwargs).distinct()
        if order_by:
            records = records.order_by(*order_by)

        return records[paginator.offset:paginator.limit] if paginator else records

        # return self.fast_related_loading(  # Предзагрузка связанных сущностей
        #     queryset=records[paginator.offset:paginator.limit] if paginator else records,
        # )


class MessagesRepository(MasterRepository):
    model = Message
