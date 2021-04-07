from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from django.db.models import Prefetch, Count, Max, Lookup, Field
from django.db.models.functions.datetime import TruncBase
from django.utils.timezone import now
from djangorestframework_camel_case.util import camelize

from app_chats.models import Chat, Message, ChatUser, MessageStat
from app_chats.versions.v1_0.serializers import MessagesSerializer, ChatSerializer
from app_market.models import Shop, Vacancy
from app_media.enums import MediaType, MediaFormat
from app_media.models import MediaModel
from app_media.versions.v1_0.repositories import MediaRepository
from app_users.enums import AccountType
from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import ProfileRepository
from backend.errors.enums import RESTErrors
from backend.errors.exceptions import EntityDoesNotExistException
from backend.errors.http_exceptions import HttpException
from backend.mixins import MasterRepository


class TruncMilliecond(TruncBase):
    """
        Отсутствующий в Django класс для миллисекунд
    """
    kind = 'millisecond'


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
        self.unread_count_expression = Count('id')
        self.last_message_created_at_expression = Max(
            # Округляем до миллисекунд, так как в бд DateTimeField хранит с точностью до МИКРОсекунд
            TruncMilliecond('messages__created_at')
        )
        # Основная часть запроса, содержащая вычисляемые поля
        self.base_query = self.model.objects.filter(users__in=[self.me]).annotate(
            unread_count=self.unread_count_expression,
            last_message_created_at=self.last_message_created_at_expression  # Нужен для сортировки и фильтрации чатов
        )

    def modify_kwargs(self, kwargs, order_by):
        need_to_create = False

        user_id = kwargs.pop('user_id', None)
        shop_id = kwargs.pop('shop_id', None)
        vacancy_id = kwargs.pop('vacancy_id', None)
        created_at = kwargs.pop('last_message_created_at', None)  # Неважно когда создан чат, важно - посл. сообщение

        checking_kwargs = {}

        # Данные для создаваемого чата
        users = []
        title = None
        target_id = None
        target_ct = None
        subject_user = None
        # ##

        if '-last_message_created_at' in order_by and created_at:
            kwargs.update({
                'last_message_created_at__lte': created_at
            })
        if 'last_message_created_at' in order_by and created_at:
            kwargs.update({
                'last_message_created_at__gte': created_at
            })

        if self.me.account_type == AccountType.MANAGER.value:  # Если роль менеджера
            # Запрашивается чат с пользователем по вакансии, если тот откликнулся на нее
            # TODO проверка на отклик по вакансии
            if user_id and vacancy_id:
                need_to_create = True
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

        elif self.me.account_type == AccountType.SELF_EMPLOYED.value:  # Если роль самозанятого
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
                users = [
                    subject_user,
                    # TODO менеджер добавляется в чат на других этапах, при создании чата неизвестно кто присоединится
                ]
            elif vacancy_id:  # user-vacancy
                need_to_create = True
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

        return checking_kwargs, need_to_create, chat_data

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
        checking_kwargs, need_to_create, chat_data = self.modify_kwargs(kwargs, order_by)

        if not self.base_query.filter(**checking_kwargs).exists() and need_to_create:
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

        return self.fast_related_loading(  # Предзагрузка связанных сущностей
            queryset=records[paginator.offset:paginator.limit] if paginator else records,
        )

    def get_by_id(self, record_id):
        records = self.base_query.filter(id=record_id)
        record = self.fast_related_loading(records).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')
        return record

    def get_chat_for_all_participants(self, record_id):
        """ Возвращает массив сериализованных чатов и сокеты для каждого участника, самих участников """
        record = self.model.objects.filter(users__in=[self.me], id=record_id)
        record = self.fast_related_loading(record).first()
        if not record:
            raise HttpException(
                status_code=RESTErrors.NOT_FOUND.value,
                detail=f'Объект {self.model._meta.verbose_name} с ID={record_id} не найден')

        prepared_data = []
        users = record.users.all()
        for user in users:
            all_other_messages = len(
                list(filter(lambda x, u=user: x.user_id == u.id, record.prefetched_messages))
            )
            all_other_messages_read = len(
                list(filter(lambda x, u=user:
                            x.user_id == u.id and getattr(x, 'stats', None) and x.stats.is_read,
                            record.prefetched_messages
                            ))
            )

            prepared_data.append({
                'sockets': [s.socket_id for s in user.sockets.all()],
                'chat': camelize(
                    ChatSerializer(record, many=False, context={
                        'me': user,
                        'unread_count': all_other_messages - all_other_messages_read
                    }).data
                )
            })

        return prepared_data, users

    @staticmethod
    def fast_related_loading(queryset, point=None):
        """ Подгрузка зависимостей с 3 уровнями вложенности по ForeignKey + GenericRelation
            -> Last_message
            -> Users
                -> Media + Sockets
        """
        queryset = queryset.prefetch_related(
            # Подгрузка сообщений
            Prefetch(
                'messages',
                queryset=Message.objects.select_related('stats').order_by('-id'),
                to_attr='prefetched_messages'
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
                            type=MediaType.AVATAR.value,
                            owner_ct_id=ContentType.objects.get_for_model(UserProfile).id,
                            format=MediaFormat.IMAGE.value
                        ),
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

        return queryset


class AsyncChatsRepository(ChatsRepository):
    def __init__(self, me=None) -> None:
        self.me = me
        super().__init__(self.me)

    @database_sync_to_async
    def get_by_id(self, record_id):
        return super().get_by_id(record_id)

    @database_sync_to_async
    def get_chat_for_all_participants(self, chat_id):
        return super().get_chat_for_all_participants(chat_id)

    @database_sync_to_async
    def check_connection_to_group(self, record_id):
        record = self.model.objects.filter(id=record_id).prefetch_related('users').first()
        if not record:
            raise EntityDoesNotExistException

        if not record.users.filter(pk=self.me.id).exists():
            # TODO расширенная логика проверки присоединения к группе
            # Если не участник чата
            return False
        return True


class CustomLookupBase(Lookup):
    # Кастомный lookup
    lookup_name = 'custom'
    parametric_string = "%s <= %s AT TIME ZONE timezone"

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return self.parametric_string % (lhs, rhs), params


@Field.register_lookup
class MSLteContains(CustomLookupBase):
    # Кастомный lookup для фильтрации DateTime по миллисекундам (в бд записи с точностью до МИКРОсекунд)
    lookup_name = 'ms_lte'
    parametric_string = "DATE_TRUNC('millisecond', %s)::TIMESTAMPTZ <= %s"


@Field.register_lookup
class MSGteContains(CustomLookupBase):
    # Кастомный lookup для фильтрации DateTime по миллисекундам (в бд записи с точностью до МИКРОсекунд)
    lookup_name = 'ms_gte'
    parametric_string = "DATE_TRUNC('millisecond', %s)::TIMESTAMPTZ >= %s"


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


class AsyncMessagesRepository(MessagesRepository):
    def __init__(self, me=None) -> None:
        self.me = me
        super().__init__(self.me)

    @database_sync_to_async
    def save_client_message(self, chat_id, content):
        message = self.model.objects.create(
            user=self.me,
            chat_id=chat_id,
            uuid=content.get('uuid'),
            message_type=content.get('messageType'),
            text=content.get('text'),
            command_data=content.get('commandData'),
        )

        attachments = content.get('attachments')
        if attachments:
            MediaRepository().reattach_files(
                uuids=attachments,
                current_model=self.me,
                current_owner_id=self.me.id,
                target_model=self.model,
                target_owner_id=message.id
            )

        # TODO сделать prefetch для attachments
        return camelize(MessagesSerializer(message, many=False).data)

    @database_sync_to_async
    def read_client_message(self, chat_id, content):
        message = self.model.objects.filter(
            chat_id=chat_id,
            uuid=content.get('uuid')
        ).exclude(
            user=self.me  # Не читаем свои сообщения
        ).first()

        data = None
        author = None

        if message:
            author = message.user
            message.read_at = now()
            message.save()

            stat = MessageStat.objects.filter(
                message=message,
                user=self.me
            ).first()

            if stat:
                stat.is_read = True
                stat.save()
            else:
                MessageStat.objects.create(
                    message=message,
                    user=self.me,
                    is_read=True
                )

            data = camelize(MessagesSerializer(message, many=False, context={
                'me': message.user
            }).data)

        return data, author
