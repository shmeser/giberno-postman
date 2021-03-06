import uuid

from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import Prefetch, Count, Max, Q, Subquery, OuterRef, Case, When, F, IntegerField, \
    Exists, Sum, Window, Value
from django.db.models.functions import Coalesce
from django.db.models.query import prefetch_related_objects
from django.utils.timezone import now
from djangorestframework_camel_case.util import camelize, underscoreize

from app_chats.enums import ChatManagerState
from app_chats.models import Chat, Message, ChatUser, MessageStat
from app_chats.versions.v1_0.serializers import MessagesSerializer, FirstUnreadMessageSerializer, \
    SocketChatSerializer
from app_market.models import Shop, Vacancy, Distributor
from app_market.versions.v1_0.repositories import ShiftAppealsRepository, VacanciesRepository
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_media.versions.v1_0.repositories import MediaRepository
from app_users.enums import AccountType
from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import ProfileRepository
from backend.errors.enums import RESTErrors
from backend.errors.exceptions import EntityDoesNotExistException, ForbiddenException
from backend.errors.http_exceptions import HttpException
from backend.mixins import MasterRepository
from backend.utils import chained_get, ArrayRemove, datetime_to_timestamp, TruncMilliecond


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
        self.unread_count_expression = Coalesce(  # Если ниче не найдено то вместо null ставим 0
            Subquery(
                Message.objects.filter(
                    chat=OuterRef('id')
                ).exclude(
                    user=self.me
                ).exclude(
                    stats__user=self.me, stats__is_read=True
                ).values('chat').annotate(
                    count=Count('pk')
                ).values('count')
            ),
            0
        )

        self.last_message_created_at_expression = Max(
            # Округляем до миллисекунд, так как в бд DateTimeField хранит с точностью до МИКРОсекунд
            TruncMilliecond('messages__created_at')
        )

        self.blocked_at_expression = Subquery(
            ChatUser.objects.filter(chat=OuterRef('id'), user=OuterRef('subject_user')).values('blocked_at')[:1]
        )

        self.active_managers_ids_expression = ArrayRemove(
            ArrayAgg('active_managers__id', distinct=True), None
        )

        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.filter(users=self.me).annotate(
            active_managers_ids=self.active_managers_ids_expression,
            blocked_at=self.blocked_at_expression,
            unread_count=self.unread_count_expression,
            last_message_created_at=self.last_message_created_at_expression  # Нужен для сортировки и фильтрации чатов
        )

    @staticmethod
    def modify_kwargs(kwargs, order_by):
        created_at = kwargs.pop('last_message_created_at', None)  # Неважно когда создан чат, важно - посл. сообщение

        if '-last_message_created_at' in order_by and created_at:
            kwargs.update({
                'last_message_created_at__lte': created_at
            })
        if 'last_message_created_at' in order_by and created_at:
            kwargs.update({
                'last_message_created_at__gte': created_at
            })

    def check_conditions_for_manager(self, user_id, vacancy_id, appeal_id):
        is_relevant_manager = False
        need_to_create = False
        users = []
        target_id = None
        target_ct = None
        subject_user = None

        # Запрашивается чат с пользователем по вакансии, если тот откликнулся на нее
        if user_id and vacancy_id:
            need_to_create = True
            # Цель обсуждения в чате - вакансия
            target_ct = ContentType.objects.get_for_model(Vacancy)
            target_id = vacancy_id
            # Основной пользователь в чате - самозанятый
            subject_user = ProfileRepository().get_by_id_and_type(user_id, AccountType.SELF_EMPLOYED.value)
            # Участники чата
            users = [
                self.me,
                subject_user
            ]
            # Проверяем есть ли такой пользователь и есть ли от него отклики на указанную вакансию
            appeal_exists = ShiftAppealsRepository.check_if_active_appeal(vacancy_id=vacancy_id, applier_id=user_id)
            if not subject_user or not appeal_exists:
                need_to_create = False
            if appeal_exists:
                # Если есть заявка, и я - релевантный менеджер для этой вакансии, добавляем в чат себя
                managers = VacanciesRepository(me=self.me).get_vacancy_managers(vacancy_id)
                if self.me in managers:
                    is_relevant_manager = True

        # Запрашивается чат с пользователем по отклику на вакансию, если тот откликнулся на нее
        if appeal_id:
            need_to_create = True
            # Проверяем есть ли отклик
            try:
                target_ct = ContentType.objects.get_for_model(Vacancy)
                appeal = ShiftAppealsRepository(me=self.me).get_by_id_for_manager(appeal_id)
                is_relevant_manager = True
                # Цель обсуждения в чате - вакансия
                target_id = appeal.shift.vacancy.id
                # Основной пользователь в чате - самозанятый
                subject_user = appeal.applier
                # Участники чата
                users = [
                    self.me,
                    subject_user
                ]
            except Exception:
                # Если нет заявки или не являюсь релевантным менеджером
                need_to_create = False

        return need_to_create, users, target_ct, target_id, subject_user, is_relevant_manager

    def check_conditions_for_self_employed(self, user_id, vacancy_id, shop_id, kwargs, checking_kwargs):
        need_to_create = False
        users = []
        target_id = None
        target_ct = None
        subject_user = None

        if user_id:  # user-user
            # Цели обсуждения в чате нет по умолчанию для такого чата
            # Участники чата
            # TODO чат с самим собой?
            users = [
                self.me,
                ProfileRepository().get_by_id(user_id)
            ]

            upd = {
                'users__in': users,
            }
            kwargs.update(upd)
            checking_kwargs.update(upd)

        elif shop_id:  # user-shop
            need_to_create = True
            # Цель обсуждения в чате - магазин
            target_ct = ContentType.objects.get_for_model(Shop)
            target_id = shop_id
            # Основной пользователь в чате - самозанятый
            subject_user = self.me
            # Участники чата
            # Все менеджеры магазина
            # shop_managers = ShopsRepository().get_managers(shop_id)
            # TODO менеджеры добавляются после просьбы пользователя о разговоре с человеком
            users = [subject_user]
        elif vacancy_id:  # user-vacancy
            need_to_create = True
            # Цель обсуждения в чате - вакансия
            target_ct = ContentType.objects.get_for_model(Vacancy)
            target_id = vacancy_id
            # Основной пользователь в чате - самозанятый
            subject_user = self.me
            # Участники чата
            # Все менеджеры магазина, в котором размещена вакансия
            # TODO менеджеры добавляются после просьбы пользователя о разговоре с человеком
            # vacancy_managers = VacanciesRepository().get_vacancy_managers(vacancy_id)
            users = [subject_user]

        return need_to_create, users, target_ct, target_id, subject_user

    def check_conditions_for_chat_creation(self, kwargs):
        need_to_create = False
        is_relevant_manager = False

        user_id = kwargs.pop('user_id', None)
        shop_id = kwargs.pop('shop_id', None)
        vacancy_id = kwargs.pop('vacancy_id', None)
        appeal_id = kwargs.pop('appeal_id', None)

        checking_kwargs = {}

        # Данные для создаваемого чата
        users = []
        title = None
        target_id = None
        target_ct = None
        subject_user = None
        # ##

        if self.me.account_type == AccountType.MANAGER.value:  # Если роль менеджера
            need_to_create, users, target_ct, target_id, subject_user, is_relevant_manager = self.check_conditions_for_manager(
                user_id, vacancy_id, appeal_id)

        elif self.me.account_type == AccountType.SELF_EMPLOYED.value:  # Если роль самозанятого
            need_to_create, users, target_ct, target_id, subject_user = self.check_conditions_for_self_employed(
                user_id, vacancy_id, shop_id, kwargs, checking_kwargs)

        target_ct_id = None
        target_ct_name = None

        updater = {}
        if subject_user:
            updater.update({
                'subject_user': subject_user
            })

        if target_ct:
            target_ct_id = target_ct.id
            target_ct_name = target_ct.model
            updater.update({
                'target_ct_id': target_ct_id,
                'target_id': target_id
            })

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

        return checking_kwargs, need_to_create, chat_data, is_relevant_manager

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
        self.modify_kwargs(kwargs, order_by)
        # Проверяем условия для создания чата
        checking_kwargs, should_create, chat_data, is_relevant_manager = self.check_conditions_for_chat_creation(kwargs)

        found_chats = self.model.objects.filter(**checking_kwargs)
        if found_chats and is_relevant_manager:
            # Если релевантный менеджер для найденных чатов, то добавляем себя в чаты
            for chat in found_chats:
                ChatUser.objects.get_or_create(chat=chat, user=self.me)

        if not found_chats and should_create:
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
            if self.me.account_type == AccountType.MANAGER.value:
                # Многоуровневая сортировка для менеджеров
                records = records.annotate(
                    manager_order=Case(
                        When(  # Первая подгруппа - нужен ответ человека
                            Q(state=ChatManagerState.NEED_MANAGER.value), then=Value(0)
                        ),
                        When(  # Вторая подгруппа - активный менеджер я
                            Q(state=ChatManagerState.MANAGER_CONNECTED, active_managers=self.me), then=Value(1)
                        ),
                        When(  # Третья подгруппа - активный менеджер НЕ я
                            Q(
                                Q(state=ChatManagerState.MANAGER_CONNECTED) &
                                ~Q(active_managers=self.me)
                            ),
                            then=Value(2)
                        ),
                        When(  # Четвертая подгруппа - общение с ботом
                            Q(state=ChatManagerState.BOT_IS_USED.value), then=Value(3)
                        ),
                        output_field=IntegerField(),
                    )
                )
                order_by = ['manager_order'] + order_by

            records = records.order_by(*order_by)

        records = self.prefetch_first_unread_message(records)
        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
        )

    def get_by_id(self, record_id):
        record = self.model.objects.filter(id=record_id).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')
        return record

    def get_chat(self, record_id):
        # При запросе чата по вакансии или по магазину релевантным менеджером, добавляем его в чат
        if self.me.account_type == AccountType.MANAGER.value:
            chat = self.model.objects.filter(id=record_id).first()
            if chat and self.check_if_staff_or_participant(chat):  # Если являюсь релевантным менеджером
                # Добавляем себя в список участников чата
                ChatUser.objects.get_or_create(chat=chat, user=self.me)

        records = self.base_query.filter(id=record_id)
        records = self.prefetch_first_unread_message(records)
        record = self.fast_related_loading(records).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')
        return record

    def get_chat_unread_count_and_first_unread(self, record_id):
        records = self.base_query.filter(id=record_id)
        records = self.prefetch_first_unread_message(records)
        record = records.first()
        if record:
            chats_unread_messages_count = self.get_all_chats_unread_count()
            first_unread_message = record.first_unread_messages[0] if record.first_unread_messages else None
            return record.unread_count, first_unread_message, chats_unread_messages_count, record.blocked_at, record.state
        else:
            return None, None, None, None, None

    @staticmethod
    def get_chat_unread_data_for_all_participants(chat, users):
        unread_counts_for_users = users.annotate(
            unread_count=Coalesce(  # Количество непрочитанных в определенном чате
                Subquery(
                    Message.objects
                        .filter(chat=chat)
                        .exclude(user=OuterRef('id'))
                        .exclude(stats__user=OuterRef('id'), stats__is_read=True)
                        .values('chat')
                        .annotate(count=Count('pk'))
                        .values('count')
                ),
                0),
            first_unread_message_uuid=Subquery(
                Message.objects.filter(chat=chat).exclude(
                    Q(
                        user=OuterRef('id'),  # Отсекаем свои сообщения
                    ) |  # или
                    Q(
                        stats__user=OuterRef('id'), stats__is_read=True  # Отсекаем те что я прочитал
                    )
                ).order_by('id').values('uuid')[:1]
            ),
            first_unread_message_created_at=Subquery(
                Message.objects.filter(chat=chat).exclude(
                    Q(
                        user=OuterRef('id'),  # Отсекаем свои сообщения
                    ) |  # или
                    Q(
                        stats__user=OuterRef('id'), stats__is_read=True  # Отсекаем те что я прочитал
                    )
                ).order_by('id').values('created_at')[:1]
            ),
            chats_unread_messages_count=Coalesce(
                Subquery(  # Проблемно через ORM посчитать для всех чатов т.к. Count() и .count() несовместим с Subquery
                    Message.objects
                        .filter(
                        Q(chat__users=OuterRef('id'), chat__users__account_type=AccountType.SELF_EMPLOYED.value) |
                        Q(
                            chat__users=OuterRef('id'),
                            chat__users__account_type=AccountType.MANAGER.value,
                            chat__state=ChatManagerState.NEED_MANAGER.value
                        ) | Q(chat__active_managers=OuterRef('id')))
                        .exclude(user=OuterRef('id'))
                        .exclude(stats__user=OuterRef('id'), stats__is_read=True)
                        .annotate(count=Window(expression=Count('id'), partition_by=[F('chat__users__id')]))
                        .values('count')[:1]  # В каждой строчке результата будет число всех строк, берем только его
                ),  # Используем оконные функции OVER с Count()
                0),
        )

        result = {}
        for u in unread_counts_for_users:
            result[f'user{u.id}'] = {
                'unread_count': u.unread_count,
                'chats_unread_messages_count': u.chats_unread_messages_count,
                'first_unread_message': {
                    'uuid': str(u.first_unread_message_uuid),
                    'createdAt': datetime_to_timestamp(u.first_unread_message_created_at),
                } if u.first_unread_message_uuid else None
            }

        return result

    def get_chat_for_all_participants(self, record_id):
        """ Возвращает массив сериализованных чатов и сокеты для каждого участника, и самих участников """
        records = self.model.objects.filter(id=record_id)
        records = self.fast_related_loading(records)
        record = records.annotate(
            blocked_at=self.blocked_at_expression
        ).first()

        if not record:
            raise EntityDoesNotExistException

        prepared_data = []
        users = record.users.all()

        push_title_for_non_owner = ''

        # Если автор - менеджер или бот - название вакансии, магазина
        if not self.me or self.me.account_type != AccountType.SELF_EMPLOYED.value:
            push_title_for_non_owner = f'{record.target.title}' if record.target else ''

        # Если автор - смз, то его имя фамилия
        if self.me and self.me.account_type == AccountType.SELF_EMPLOYED.value:
            push_title_for_non_owner = f'{self.me.first_name} {self.me.last_name}'

        unread_data_dict = self.get_chat_unread_data_for_all_participants(record, users)

        active_managers_ids = [am.id for am in record.active_managers.all()]
        inactive_managers_ids = []

        for user in users:
            # Собираем ид неактивных менеджеров
            if user.account_type == AccountType.MANAGER.value and user.id not in active_managers_ids:
                inactive_managers_ids.append(user.id)

            prepared_data.append({
                'sockets': [s.socket_id for s in user.sockets.all()],
                'chat': camelize(
                    SocketChatSerializer(record, many=False, context={
                        'me': user,
                        'unread_count': chained_get(
                            unread_data_dict, f'user{user.id}', 'unread_count',
                            default=None
                        ),
                        'first_unread_message': chained_get(
                            unread_data_dict, f'user{user.id}', 'first_unread_message',
                            default=None
                        )
                    }).data
                ),
                'chats_unread_messages': chained_get(
                    unread_data_dict, f'user{user.id}', 'chats_unread_messages_count',
                    default=None
                ),
            })

        return prepared_data, users, push_title_for_non_owner, inactive_managers_ids

    @staticmethod
    def fast_related_loading(queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
            -> Last_message
            -> Users
                -> Media + Sockets
        """
        queryset = queryset.prefetch_related(
            # Подгрузка последних сообщений #
            Prefetch(
                'messages',
                queryset=Message.objects.prefetch_related('stats').order_by(
                    'chat_id', '-id'  # Сортируем по ид по убыванию, чтоб в distinct попали последние сообщения
                ).distinct('chat_id'),  # Нужно по 1 последнему сообщению для каждого чата
                to_attr='last_messages'
            )
        ).prefetch_related(
            # Подгрузка участников чата
            Prefetch(
                'users',
                queryset=UserProfile.objects.filter(
                    deleted=False
                ).prefetch_related(
                    # Подгрузка медиа для профилей
                    Prefetch(
                        'media',
                        queryset=MediaModel.objects.filter(
                            deleted=False,
                            type=MediaType.AVATAR.value,
                            owner_ct_id=ContentType.objects.get_for_model(UserProfile).id,
                            format=MediaFormat.IMAGE.value
                        ).order_by('-created_at'),  # Сортировка по дате обязательно
                        to_attr='medias'
                    ),
                ).prefetch_related(
                    # Подгрузка сокетов для определения online|offline
                    'sockets',
                )
            )
        ).select_related(
            'subject_user'
        ).prefetch_related(
            'target'
        )

        # Префетчим логотипы торговых сетей для target, который Generic Relation
        shop_ct = ContentType.objects.get_for_model(Shop)
        chats_on_shops = [item for item in queryset if item.target_ct_id == shop_ct.id]
        if chats_on_shops:
            prefetch_related_objects(chats_on_shops, Prefetch(
                "target__distributor__media",
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.LOGO.value,
                    owner_ct_id=ContentType.objects.get_for_model(Distributor).id,
                    format=MediaFormat.IMAGE.value
                ).order_by('-created_at'),  # Сортировка по дате обязательно
                to_attr='medias'
            ))

        vacancy_ct = ContentType.objects.get_for_model(Vacancy)
        chats_on_vacancies = [item for item in queryset if item.target_ct_id == vacancy_ct.id]
        if chats_on_vacancies:
            prefetch_related_objects(chats_on_vacancies, Prefetch(
                "target__shop__distributor__media",
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.LOGO.value,
                    owner_ct_id=ContentType.objects.get_for_model(Distributor).id,
                    format=MediaFormat.IMAGE.value
                ).order_by('-created_at'),  # Сортировка по дате обязательно
                to_attr='medias'
            ))

        return queryset

    def prefetch_first_unread_message(self, queryset):
        # Подгружаем первое непрочитанное сообщение чатов для 1 пользователя, делающего запрос
        return queryset.prefetch_related(
            Prefetch(
                'messages',
                queryset=Message.objects.exclude(
                    Q(
                        user=self.me,  # Отсекаем свои сообщения
                    ) |  # или
                    Q(
                        stats__user=self.me, stats__is_read=True  # Отсекаем те что я прочитал
                    )
                ).order_by(
                    'chat_id', 'id'
                ).distinct('chat_id'),
                # Берем 1 сообщение чата самое раннее, не прочитанное пользователем и не написанное им
                to_attr='first_unread_messages'
            )
        )

    def check_if_staff_or_participant(self, chat):
        """
        Проверка на свой чат или на релевантных менеджеров, которые имеют доступ к чатам,
        относящихся к магазину, где они сотрудники
        :param chat:
        :return:
        """
        if not chat.users.filter(pk=self.me.id).exists():
            # TODO расширенная логика проверки присоединения к группе
            # Если не участник чата, но является релевантным менеджером
            if chat.target_ct == ContentType.objects.get_for_model(Vacancy) and chat.target.shop.staff.filter(
                    pk=self.me.id).exists():
                # Если цель вакансия и являюсь менеджером магазина, в котором размещена вакансия
                return True
            if chat.target_ct == ContentType.objects.get_for_model(Shop) and chat.target.staff.filter(
                    pk=self.me.id).exists():
                # Если цель магазин и являюсь менеджером магазина
                return True
            return False
        return True

    def check_permission_for_action(self, record_id):
        record = self.model.objects.filter(id=record_id).annotate(
            blocked_at=self.blocked_at_expression
        ).first()
        if not record:
            raise EntityDoesNotExistException
        if record.blocked_at is not None or self.check_if_staff_or_participant(record) is False:
            raise ForbiddenException

    def check_if_exists(self, record_id):
        record = self.model.objects.filter(id=record_id).first()
        if not record:
            raise EntityDoesNotExistException

    def get_all_chats_unread_count(self):
        chats = self.model.objects.filter(users=self.me)

        if self.me.account_type == AccountType.MANAGER.value:  # Если менеджер
            chats = chats.filter(
                # Либо где активный менеджер - я
                Q(state=ChatManagerState.MANAGER_CONNECTED.value, active_managers=self.me) |
                # Либо где нужен менеджер
                Q(state=ChatManagerState.NEED_MANAGER.value)
            )

        return chats.annotate(unread_count=self.unread_count_expression).aggregate(
            total_unread_count=Coalesce(Sum('unread_count'), 0)
        )['total_unread_count']

    def set_me_as_active_manager(self, chat_id):
        should_send_info = False
        active_managers_ids = []

        if self.me and self.me.account_type == AccountType.MANAGER.value:
            # Если менеджер
            chat = Chat.objects.filter(pk=chat_id, deleted=False).prefetch_related('active_managers').first()

            active_managers = chat.active_managers.all()
            active_managers_ids = [am.id for am in active_managers]

            if not active_managers:
                # Если не было активного менеджера
                should_send_info = True

            # Добавляем себя в активные менеджеры
            chat.active_managers.add(self.me)
            if self.me.id not in active_managers_ids:
                active_managers_ids.append(self.me.id)
            chat.state = ChatManagerState.MANAGER_CONNECTED.value  # Переводим в состояние подключенного менеджера
            chat.save()

        return should_send_info, active_managers_ids

    def remove_active_manager(self, chat_id):
        should_send_info = False

        chat = Chat.objects.filter(pk=chat_id, deleted=False).prefetch_related('active_managers').first()

        # TODO проверить prefetched на еще один запрос
        active_managers = chat.active_managers.all()
        active_managers_count = chat.active_managers.count()
        active_managers_ids = [am.id for am in active_managers]
        if active_managers and self.me.id in active_managers_ids:
            # Если есть активный менеджер и это я
            if active_managers_count == 1:  # Если был активный менеджер только я
                should_send_info = True
                chat.state = ChatManagerState.BOT_IS_USED.value  # Переводим в состояние разгровара с ботом
                chat.save()

            chat.active_managers.remove(self.me)
            active_managers_ids.remove(self.me.id)

        return should_send_info, active_managers_ids, chat.state

    def get_managers(self, chat_id):
        shop_ct = ContentType.objects.get_for_model(Shop)
        vacancy_ct = ContentType.objects.get_for_model(Vacancy)
        record = self.model.objects.filter(pk=chat_id, deleted=False).annotate(
            blocked_at=self.blocked_at_expression
        ).first()
        managers = None
        if record:
            # TODO учитывать настройки отпуска у менеджеров
            if record.target_ct == shop_ct:
                managers = record.target.staff.filter(account_type=AccountType.MANAGER.value)
            if record.target_ct == vacancy_ct:
                managers = record.target.shop.staff.filter(account_type=AccountType.MANAGER.value)

        return managers, record.blocked_at

    def get_managers_and_sockets(self, chat_id):
        managers, blocked_at = self.get_managers(chat_id)
        sockets = []
        if managers:
            sockets = managers.aggregate(
                sockets=ArrayRemove(ArrayAgg('sockets__socket_id'), None)
            )['sockets']

        return managers, sockets, blocked_at

    def block_chat(self, record_id):
        # Блокировка чата для смз
        chat = self.model.objects.filter(id=record_id).first()
        if not chat:
            raise EntityDoesNotExistException

        if self.check_if_staff_or_participant(chat):
            ChatUser.objects.filter(user=chat.subject_user, chat=chat).update(
                updated_at=now(),
                blocked_at=now()
            )
            return self.get_chat(record_id)  # Используем для вычисляемых полей
        else:
            raise ForbiddenException

    def unblock_chat(self, record_id):
        chat = self.model.objects.filter(id=record_id).first()
        if not chat:
            raise EntityDoesNotExistException

        if self.check_if_staff_or_participant(chat):
            ChatUser.objects.filter(user=chat.subject_user, chat=chat).update(
                updated_at=now(),
                blocked_at=None
            )
            return self.get_chat(record_id)  # Используем для вычисляемых полей
        else:
            raise ForbiddenException

    def market_data(self, record_id):
        chat = self.model.objects.filter(id=record_id).first()
        if not chat:
            raise EntityDoesNotExistException

        if self.check_if_staff_or_participant(chat):
            # Если предмет чата - магазин
            if chat.target and isinstance(chat.target, Shop):
                return {
                    'vacancy_id': None,
                    'shop_id': chat.target_id,
                    'distributor_id': chat.target.distributor_id
                }
            # Если предмет чата - ва
            if chat.target and isinstance(chat.target, Vacancy):
                return {
                    'vacancy_id': chat.target_id,
                    'shop_id': chat.target.shop_id,
                    'distributor_id': chat.target.shop.distributor_id
                }
            return {
                'vacancy_id': None,
                'shop_id': None,
                'distributor_id': None
            }
        else:
            raise ForbiddenException


class AsyncChatsRepository(ChatsRepository):
    def __init__(self, me=None) -> None:
        self.me = me
        super().__init__(self.me)

    @database_sync_to_async
    def get_by_id(self, record_id):
        return super().get_by_id(record_id)

    @database_sync_to_async
    def get_chat(self, record_id):
        return super().get_chat(record_id)

    @database_sync_to_async
    def get_chat_for_all_participants(self, chat_id):
        return super().get_chat_for_all_participants(chat_id)

    @database_sync_to_async
    def check_permission_for_action(self, record_id):
        return super().check_permission_for_action(record_id)

    @database_sync_to_async
    def check_if_exists(self, record_id):
        return super().check_if_exists(record_id)

    @database_sync_to_async
    def get_all_chats_unread_count(self):
        return super().get_all_chats_unread_count()

    @database_sync_to_async
    def set_me_as_active_manager(self, chat_id):
        return super().set_me_as_active_manager(chat_id)

    @database_sync_to_async
    def remove_active_manager(self, chat_id):
        return super().remove_active_manager(chat_id)

    @database_sync_to_async
    def get_managers_and_sockets(self, chat_id):
        return super().get_managers_and_sockets(chat_id)


class MessagesRepository(MasterRepository):
    model = Message

    def __init__(self, me=None, chat_id=None) -> None:
        super().__init__()

        self.me = me
        self.chat_id = chat_id

        # Выражения для вычисляемых полей в annotate
        self.unread_count_expression = Count('id')
        self.last_message_created_at_expression = Max(
            # Округляем до миллисекунд, так как в бд DateTimeField хранит с точностью до МИКРОсекунд
            TruncMilliecond('messages__created_at')
        )
        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.filter(
            chat__users__in=[self.me],  # Должен быть в списке пользователей
            chat_id=self.chat_id  # Сообщения искомого чата
        )

    def modify_kwargs(self, kwargs, order_by):

        created_at = kwargs.pop('created_at', None)  # Неважно когда создан чат, важно - посл. сообщение

        # Используем кастомные lookups ms_lte и ms_lte для точной фильтрации по DateTime
        if '-created_at' in order_by and created_at:
            kwargs.update({
                'created_at__ms_lte': created_at
            })
        if 'created_at' in order_by and created_at:
            kwargs.update({
                'created_at__ms_gte': created_at
            })

    @staticmethod
    def fast_related_loading(queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
            -> Media (attachments)
            -> User + Media
        """
        queryset = queryset.select_related(
            'user',
        ).prefetch_related(
            # Подгрузка медиа для профилей
            Prefetch(
                'user__media',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.AVATAR.value,
                    owner_ct_id=ContentType.objects.get_for_model(UserProfile).id,
                    format=MediaFormat.IMAGE.value
                ),
                to_attr='medias'
            )
        ).prefetch_related(
            # Подгрузка медиа для сообщений
            Prefetch(
                'attachments',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.ATTACHMENT.value,
                    owner_ct_id=ContentType.objects.get_for_model(Message).id
                ),
                to_attr='medias'
            )
        )

        return queryset

    @staticmethod
    def fast_related_loading_sockets(queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
            -> Media (attachments)
            -> User + Media
        """
        queryset = queryset.select_related(
            'user',
        ).prefetch_related(
            # Подгрузка сокетов
            'user__sockets',
        ).prefetch_related(
            # Подгрузка медиа для сообщений
            Prefetch(
                'attachments',
                queryset=MediaModel.objects.filter(
                    deleted=False,
                    type=MediaType.ATTACHMENT.value,
                    owner_ct_id=ContentType.objects.get_for_model(Message).id
                ),
                to_attr='medias'
            )
        )

        return queryset

    def filter_by_kwargs(self, kwargs, paginator=None, order_by: list = None):
        self.modify_kwargs(kwargs, order_by)
        records = self.base_query.exclude(deleted=True).filter(**kwargs)
        if order_by:
            records = records.order_by(*order_by)

        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
        )

    def save_client_message(self, content):
        content = underscoreize(content)
        message = self.model.objects.create(  # 1
            user=self.me,
            chat_id=self.chat_id,
            uuid=content.get('uuid'),
            message_type=content.get('message_type'),
            text=content.get('text'),
        )

        # Читаем все сообщения перед созданным
        self.read_all_before(message)  # 3

        attachments = content.get('attachments')
        if attachments:
            MediaRepository().reattach_attachments(  # 1
                uuids=attachments,
                current_model=self.me,
                current_owner_id=self.me.id,
                target_model=self.model,
                target_owner_id=message.id
            )

        return message

    def get_last_message(self):
        return self.model.objects.filter(chat_id=self.chat_id).last()

    def read_all_before(self, message):
        # Прочитать все непрочитанные чужие сообщения до того сообщения, которое читается
        all_others_unread_messages = Message.objects.filter(
            chat_id=self.chat_id,
            created_at__lt=message.created_at
        ).exclude(
            user=self.me  # Исключаем мои сообщения
        ).annotate(
            # Моя статистика существует
            my_stat_exists=Exists(MessageStat.objects.filter(message_id=OuterRef('pk'), user=self.me)),
            # В моей статистике стоит флаг is_read=True
            my_stat_is_read=Exists(MessageStat.objects.filter(message_id=OuterRef('pk'), user=self.me, is_read=True))
        ).aggregate(
            stats_isnull=ArrayRemove(
                ArrayAgg(
                    Case(
                        When(
                            my_stat_exists=False,
                            then=F('id')
                        ),
                        default=None,
                        output_field=IntegerField()
                    )
                ),
                None  # Удаляем null'ы из массива
            ),
            is_read_false=ArrayRemove(
                ArrayAgg(
                    Case(
                        When(
                            my_stat_exists=True,
                            my_stat_is_read=False,
                            then=F('id')
                        ),
                        default=None,
                        output_field=IntegerField()
                    )
                ),
                None  # Удаляем null'ы из массива
            ),
        )

        # Проставляем read_at в непрочтенные никем сообщения
        Message.objects.filter(
            chat_id=self.chat_id,
            created_at__lt=message.created_at,
            read_at__isnull=True  # Непрочитанные никем
        ).exclude(
            user=self.me
        ).update(
            read_at=now()
        )

        # Проверяем свою статистику
        if all_others_unread_messages['stats_isnull']:
            # Все непрочитанные сообщения без моей статистики по ним
            create_stats_links = []
            for m_id in all_others_unread_messages['stats_isnull']:
                create_stats_links.append(MessageStat(user=self.me, message_id=m_id, is_read=True))

            if create_stats_links:
                MessageStat.objects.bulk_create(create_stats_links)  # Массовое создание статистики по сообщениям

        if all_others_unread_messages['is_read_false']:
            # Все непрочитанные с имеющейся моей статистикой по ним
            MessageStat.objects.filter(
                message__id__in=all_others_unread_messages['is_read_false'],
                user=self.me
            ).update(
                is_read=True
            )

    def read_message(self, content, prefetch=False):
        """
        :param content:
        :param prefetch: Сделать предзагрузку данных для автора сообщения и его сокетов
        :return:
        """

        msg_owner = None
        msg_owner_sockets = []
        should_response_owner = False

        messages = self.model.objects.filter(
            chat_id=self.chat_id,
            uuid=content.get('uuid')
        ).exclude(
            user=self.me  # Не читаем свои сообщения
        )

        if prefetch:
            message = self.fast_related_loading_sockets(messages).first()
        else:
            message = messages.first()

        if message:
            msg_owner = message.user
            msg_owner_sockets = [s.socket_id for s in msg_owner.sockets.all()] if prefetch and msg_owner else []

            # Читаем все предыдущие сообщения
            self.read_all_before(message)

            if not message.read_at:  # Если сообщение ранее никем не прочитано
                message.read_at = now()
                message.save()
                should_response_owner = True

            stat = MessageStat.objects.filter(
                message=message,
                user=self.me
            ).first()

            if stat:
                if not stat.is_read:  # Не читаем заново от имени своего пользователя = не делаем лишний запрос на save
                    stat.is_read = True
                    stat.save()
            else:
                MessageStat.objects.create(
                    message=message,
                    user=self.me,
                    is_read=True
                )

        return message, msg_owner, msg_owner_sockets, should_response_owner

    def save_bot_message(self, content):
        content = underscoreize(content)
        message = self.model.objects.create(  # 1
            user=None,
            chat_id=self.chat_id,
            uuid=uuid.uuid4(),
            message_type=content.get('message_type'),
            icon_type=content.get('icon_type'),
            title=content.get('title'),
            text=content.get('text'),
            buttons=content.get('buttons')
        )

        # TODO общие файлы для сообщений сделать
        # attachments = content.get('attachments')
        # if attachments:
        #     MediaRepository().reattach_files(  # 1
        #         uuids=attachments,
        #         current_model=self.me,
        #         current_owner_id=self.me.id,
        #         target_model=self.model,
        #         target_owner_id=message.id
        #     )

        return camelize(MessagesSerializer(message, many=False).data)


class AsyncMessagesRepository(MessagesRepository):
    def __init__(self, me=None, chat_id=None) -> None:
        self.me = me
        self.chat_id = chat_id
        super().__init__(self.me, self.chat_id)

    @database_sync_to_async
    def save_client_message(self, content):
        message = super().save_client_message(content)
        # TODO сделать prefetch для attachments
        return camelize(MessagesSerializer(message, many=False).data)

    @database_sync_to_async
    def client_read_message(self, content):
        return super().read_message(
            content=content, prefetch=True
        )

    @database_sync_to_async
    def get_unread_data(self, message, msg_owner, should_response_owner):

        owner_unread_count = None
        owner_first_unread_serialized = None
        owner_chats_unread_count = None
        my_first_unread_message_serialized = None

        last_msg = super().get_last_message()  # TODO проверить инициализацию

        # Количество непрочитанных сообщений в чате для себя
        my_unread_count, my_first_unread_message, my_chats_unread_count, blocked_at, state = ChatsRepository(
            me=self.me).get_chat_unread_count_and_first_unread(self.chat_id)

        serialized_message = camelize(MessagesSerializer(message, many=False).data)

        if my_first_unread_message:
            my_first_unread_message_serialized = camelize(
                FirstUnreadMessageSerializer(my_first_unread_message, many=False).data)

        if last_msg and last_msg.id == message.id and should_response_owner:
            # Если последнее сообщение в чате и не было прочитано ранее, то запрашиваем число непрочитанных для чата
            # Т.к. отправляем данные о прочитанном сообщении в событии SERVER_CHAT_LAST_MSG_UPDATED, то нужны данные
            # по unread_count
            owner_unread_count, owner_first_unread, owner_chats_unread_count, blocked_at, state = ChatsRepository(
                me=msg_owner
            ).get_chat_unread_count_and_first_unread(self.chat_id)

            owner_first_unread_serialized = camelize(
                FirstUnreadMessageSerializer(owner_first_unread, many=False).data
            ) if owner_first_unread else None

        return (
            serialized_message,
            owner_unread_count,
            owner_first_unread_serialized,
            owner_chats_unread_count,
            my_unread_count,
            my_first_unread_message_serialized,
            my_chats_unread_count,
            blocked_at,
            state
        )

    @database_sync_to_async
    def save_bot_message(self, content):
        return super().save_bot_message(content)
